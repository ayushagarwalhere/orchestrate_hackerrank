"""Opt-in, metered inference with immutable cache provenance and hard call limits."""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
import contextlib
import hashlib
import importlib
import math
import multiprocessing
import os
from pathlib import Path
import re
import time
from typing import Callable, Protocol

from .contracts import AuditFailure, FailureType
from .model_schemas import (INTENT_SCHEMA, SCREENSHOT_SCHEMA, canonical, digest, strict_json, validate)


class Purpose(str, Enum):
    SCREENSHOT = "screenshot"
    INTENT = "ambiguous_intent"


@dataclass(frozen=True)
class PromptSpec:
    purpose: Purpose
    version: str
    text: str = field(repr=False)
    schema_version: str
    schema: dict = field(repr=False)

    @property
    def sha256(self):
        return hashlib.sha256(self.text.encode("utf-8")).hexdigest()


def default_prompts() -> dict[Purpose, PromptSpec]:
    root = Path(__file__).resolve().parents[1] / "prompts"
    return {
        Purpose.SCREENSHOT: PromptSpec(Purpose.SCREENSHOT, "screenshot.v1",
            (root / "screenshot.v1.md").read_text(encoding="utf-8"), "screenshot.records.v1", SCREENSHOT_SCHEMA),
        Purpose.INTENT: PromptSpec(Purpose.INTENT, "intent.v1",
            (root / "intent.v1.md").read_text(encoding="utf-8"), "intent.facts.v1", INTENT_SCHEMA),
    }


@dataclass(frozen=True)
class Usage:
    input_tokens: int
    output_tokens: int
    cost_microusd: int | None = None


def valid_usage(usage) -> bool:
    return (type(usage) is Usage and all(type(v) is int and v >= 0 for v in
            (usage.input_tokens, usage.output_tokens)) and
            (usage.cost_microusd is None or type(usage.cost_microusd) is int and usage.cost_microusd >= 0))


@dataclass(frozen=True)
class ModelRequest:
    purpose: Purpose
    system_prompt: str = field(repr=False)
    response_schema: dict = field(repr=False)
    untrusted_data: bytes = field(repr=False)
    mime_type: str
    max_output_tokens: int
    timeout_seconds: float
    provider: str = ""
    model: str = ""


@dataclass(frozen=True)
class ModelReply:
    provider: str
    model: str
    text: str = field(repr=False)
    usage: Usage | None = None


class ModelClient(Protocol):
    def complete(self, request: ModelRequest) -> ModelReply: ...


class ProviderFailure(Exception):
    """No message is transported. Usage is required before retrying a refusal."""
    def __init__(self, *, retryable=False, usage: Usage | None = None):
        self.retryable, self.usage = retryable, usage


@dataclass(frozen=True)
class Attempt:
    reply: ModelReply | None = None
    usage: Usage | None = None
    retryable: bool = False
    invalid_response: bool = False


def _worker(connection, client, request, max_response_bytes):
    # Third-party clients are trusted code, not instructions from the input. The
    # child process contains blocking I/O and suppresses accidental console dumps.
    with open(os.devnull, "w") as sink, contextlib.redirect_stdout(sink), contextlib.redirect_stderr(sink):
        try:
            if isinstance(client, str):
                module, factory = client.split(":")
                client = getattr(importlib.import_module(module), factory)()
            reply = client.complete(request)
            if type(reply) is not ModelReply:
                result = Attempt()
            elif not isinstance(reply.text, str) or len(reply.text.encode("utf-8")) > max_response_bytes:
                result = Attempt(usage=reply.usage, invalid_response=True)
            else:
                result = Attempt(reply, reply.usage)
        except ProviderFailure as error:
            result = Attempt(usage=error.usage, retryable=error.retryable)
        except BaseException:
            result = Attempt()
        try:
            connection.send(result)
        finally:
            connection.close()


class ProcessRunner:
    """Spawn isolates provider setup and invocation; timeout kills the worker."""
    def run(self, client, request: ModelRequest, timeout: float, max_response_bytes: int) -> Attempt:
        started = time.perf_counter()
        context = multiprocessing.get_context("spawn")
        receive, send = context.Pipe(duplex=False)
        process = context.Process(target=_worker, args=(send, client, request, max_response_bytes), daemon=True)
        try:
            process.start()
            send.close()
            remaining = timeout - (time.perf_counter() - started)
            if remaining <= 0 or not receive.poll(remaining):
                raise TimeoutError()
            return receive.recv()
        finally:
            receive.close()
            send.close()
            if process.pid is not None:
                if process.is_alive():
                    process.terminate()
                process.join(timeout=0.5)
                if process.is_alive():
                    process.kill()
                    process.join(timeout=0.5)


@dataclass(frozen=True)
class InferenceLimits:
    max_invocations: int = 32
    max_live_calls: int = 16
    max_retries: int = 1
    timeout_seconds: float = 20
    total_seconds: float = 120
    max_input_bytes: int = 16 * 1024 * 1024
    max_response_bytes: int = 65536
    max_output_tokens: int = 2048
    max_total_tokens: int = 100000

    def check(self):
        integers = (self.max_invocations, self.max_live_calls, self.max_input_bytes,
                    self.max_response_bytes, self.max_output_tokens, self.max_total_tokens)
        if (any(type(v) is not int or v < 0 for v in integers) or
                type(self.max_retries) is not int or not 0 <= self.max_retries <= 2 or
                any(type(v) not in (int, float) or not math.isfinite(v) or v <= 0
                    for v in (self.timeout_seconds, self.total_seconds))):
            raise AuditFailure(FailureType.INPUT)


@dataclass(frozen=True)
class ValidatedResponse:
    value: dict = field(repr=False)
    provenance: dict = field(repr=False)
    response_sha256: str
    cache_hit: bool


class ResponseCache:
    """Read-only historical entries; no relabeling or overwriting across prompts."""
    def __init__(self, root: Path):
        self.root = root

    def path(self, key: str) -> Path:
        if not re.fullmatch(r"[a-f0-9]{64}", key):
            raise AuditFailure(FailureType.CACHE)
        return self.root / (key + ".json")

    def read(self, key: str, maximum: int):
        path = self.path(key)
        if not path.exists():
            return None
        try:
            with path.open("rb") as stream:
                raw = stream.read(maximum + 1)
            if len(raw) > maximum:
                raise ValueError()
            return strict_json(raw.decode("utf-8"))
        except Exception:
            raise AuditFailure(FailureType.CACHE) from None

    def write(self, key: str, value: dict):
        try:
            self.root.mkdir(parents=True, exist_ok=True)
            # Exclusive creation preserves old entries even on a concurrent run.
            # Interrupted writes are corrupt entries and fail closed on replay.
            with self.path(key).open("xb") as stream:
                stream.write(canonical(value))
                stream.flush()
                os.fsync(stream.fileno())
        except Exception:
            raise AuditFailure(FailureType.CACHE) from None


class ModelRuntime:
    def __init__(self, provider: str, model: str, *, client=None, allow_live=False,
                 cache: ResponseCache | None = None, limits: InferenceLimits | None = None,
                 runner=None, clock: Callable[[], float] = time.perf_counter, prompts=None):
        if type(allow_live) is not bool or not all(isinstance(x, str) and re.fullmatch(r"[A-Za-z0-9._:/-]{1,120}", x)
                                                 for x in (provider, model)):
            raise AuditFailure(FailureType.INPUT)
        self.provider, self.model, self.client, self.allow_live = provider, model, client, allow_live
        self.cache, self.limits = cache, limits or InferenceLimits()
        self.limits.check()
        self.runner, self.clock, self.prompts = runner or ProcessRunner(), clock, prompts or default_prompts()
        self.begin_run()

    def begin_run(self):
        self.started = self.clock()
        self.invocations = self.live_calls = self.retries = self.cache_hits = 0
        self.input_tokens = self.output_tokens = self.cost = 0
        self.unknown_usage = self.unknown_cost = 0
        self.historical_input = self.historical_output = 0
        self.identity_mismatches = 0
        self.historical_calls = self.historical_cost = self.historical_unknown_cost = 0
        self.seen_cache_keys = set()

    def summary(self):
        return {"provider": self.provider, "model": self.model, "adapter_invocations": self.invocations,
                "model_calls": self.live_calls, "retries": self.retries, "cache_hits": self.cache_hits,
                "input_tokens": self.input_tokens, "output_tokens": self.output_tokens,
                "total_tokens": self.input_tokens + self.output_tokens,
                "cost_microusd": None if self.unknown_cost or self.unknown_usage or self.identity_mismatches else self.cost,
                "unmetered_attempts": self.unknown_usage,
                "usage_complete": self.unknown_usage == 0 and self.identity_mismatches == 0,
                "identity_mismatches": self.identity_mismatches,
                "cache_historical_input_tokens": self.historical_input,
                "cache_historical_output_tokens": self.historical_output,
                "cache_historical_model_calls": self.historical_calls,
                "cache_historical_cost_microusd": None if self.historical_unknown_cost else self.historical_cost}

    def _meter(self, usage):
        if not valid_usage(usage):
            self.unknown_usage += 1
            raise AuditFailure(FailureType.MODEL_USAGE)
        self.input_tokens += usage.input_tokens
        self.output_tokens += usage.output_tokens
        if usage.cost_microusd is None:
            self.unknown_cost += 1
        else:
            self.cost += usage.cost_microusd
        if self.input_tokens + self.output_tokens > self.limits.max_total_tokens:
            raise AuditFailure(FailureType.MODEL_BUDGET)

    def _cached(self, entry, metadata, key, validator):
        try:
            if (type(entry) is not dict or set(entry) != {"format_version", "key", "provenance", "response",
                    "response_sha256", "historical_usage", "attempt_usage", "created_at"} or
                    type(entry["format_version"]) is not int or entry["format_version"] != 2 or
                    entry["key"] != key or entry["provenance"] != metadata or
                    entry["response_sha256"] != digest(entry["response"]) or
                    len(canonical(entry["response"])) > self.limits.max_response_bytes or
                    type(entry["created_at"]) is not str or
                    datetime.fromisoformat(entry["created_at"]).tzinfo is None or
                    set(entry["historical_usage"]) != {"input_tokens", "output_tokens", "cost_microusd"}):
                raise ValueError()
            usage = Usage(**entry["historical_usage"])
            attempts = entry["attempt_usage"]
            if (not valid_usage(usage) or type(attempts) is not list or not 1 <= len(attempts) <= 3 or
                    any(type(item) is not dict or set(item) != {"input_tokens", "output_tokens", "cost_microusd"}
                        or not valid_usage(Usage(**item)) for item in attempts)):
                raise ValueError()
            total = Usage(sum(item["input_tokens"] for item in attempts),
                          sum(item["output_tokens"] for item in attempts),
                          None if any(item["cost_microusd"] is None for item in attempts) else
                          sum(item["cost_microusd"] for item in attempts))
            if total != usage:
                raise ValueError()
            validate(entry["response"], self.prompts[Purpose(metadata["purpose"])].schema)
            validator(entry["response"])
            self.cache_hits += 1
            if key not in self.seen_cache_keys:
                self.seen_cache_keys.add(key)
                self.historical_input += usage.input_tokens
                self.historical_output += usage.output_tokens
                self.historical_calls += len(attempts)
                if usage.cost_microusd is None:
                    self.historical_unknown_cost += 1
                else:
                    self.historical_cost += usage.cost_microusd
            return ValidatedResponse(entry["response"], metadata, entry["response_sha256"], True)
        except Exception:
            raise AuditFailure(FailureType.CACHE) from None

    def request(self, purpose: Purpose, payload: bytes, mime_type: str, binding: dict, validator) -> ValidatedResponse:
        if type(purpose) is not Purpose:
            raise AuditFailure(FailureType.MODEL_RESPONSE)
        if (type(payload) is not bytes or
                (purpose is Purpose.SCREENSHOT and (mime_type != "image/png" or
                    not payload.startswith(b"\x89PNG\r\n\x1a\n"))) or
                (purpose is Purpose.INTENT and mime_type != "text/plain")):
            raise AuditFailure(FailureType.MODEL_RESPONSE)
        if self.invocations >= self.limits.max_invocations:
            raise AuditFailure(FailureType.MODEL_BUDGET)
        self.invocations += 1
        if len(payload) > self.limits.max_input_bytes or self.clock() - self.started >= self.limits.total_seconds:
            raise AuditFailure(FailureType.MODEL_BUDGET)
        prompt = self.prompts[purpose]
        if prompt.purpose is not purpose:
            raise AuditFailure(FailureType.MODEL_RESPONSE)
        metadata = {"cache_format_version": 2, "purpose": purpose.value, "provider": self.provider, "model": self.model,
                    "prompt_version": prompt.version, "prompt_sha256": prompt.sha256,
                    "schema_version": prompt.schema_version, "schema_sha256": digest(prompt.schema),
                    "payload_sha256": hashlib.sha256(payload).hexdigest(), "binding": binding,
                    "max_output_tokens": self.limits.max_output_tokens}
        key = digest(metadata)
        if self.cache is not None:
            entry = self.cache.read(key, self.limits.max_response_bytes * 4 + 65536)
            if entry is not None:
                return self._cached(entry, metadata, key, validator)
        if not self.allow_live or self.client is None:
            raise AuditFailure(FailureType.LIVE_DISABLED)
        attempts_usage = []
        for retry in range(self.limits.max_retries + 1):
            remaining = self.limits.total_seconds - (self.clock() - self.started)
            if (remaining <= 0 or self.live_calls >= self.limits.max_live_calls or
                    self.input_tokens + self.output_tokens >= self.limits.max_total_tokens):
                raise AuditFailure(FailureType.MODEL_BUDGET)
            self.live_calls += 1
            self.retries += int(retry > 0)
            timeout = min(remaining, self.limits.timeout_seconds)
            request = ModelRequest(purpose, prompt.text, prompt.schema, payload, mime_type,
                                   self.limits.max_output_tokens, timeout, self.provider, self.model)
            try:
                attempt = self.runner.run(self.client, request, timeout, self.limits.max_response_bytes)
            except TimeoutError:
                self.unknown_usage += 1
                raise AuditFailure(FailureType.MODEL_TIMEOUT) from None
            except Exception:
                self.unknown_usage += 1
                raise AuditFailure(FailureType.PROVIDER) from None
            if type(attempt) is not Attempt:
                self.unknown_usage += 1
                raise AuditFailure(FailureType.MODEL_USAGE)
            self._meter(attempt.usage)
            attempts_usage.append(attempt.usage)
            if attempt.usage.output_tokens > self.limits.max_output_tokens:
                raise AuditFailure(FailureType.MODEL_BUDGET)
            if self.clock() - self.started > self.limits.total_seconds:
                raise AuditFailure(FailureType.MODEL_BUDGET)
            if attempt.invalid_response:
                raise AuditFailure(FailureType.MODEL_RESPONSE)
            if attempt.reply is None:
                if attempt.retryable and retry < self.limits.max_retries:
                    continue
                raise AuditFailure(FailureType.PROVIDER)
            reply = attempt.reply
            if type(reply) is not ModelReply or reply.provider != self.provider or reply.model != self.model:
                self.identity_mismatches += 1
                raise AuditFailure(FailureType.MODEL_RESPONSE)
            try:
                if (not isinstance(reply.text, str) or
                        len(reply.text.encode("utf-8")) > self.limits.max_response_bytes):
                    raise ValueError()
                value = strict_json(reply.text)
                validate(value, prompt.schema)
                validator(value)
            except Exception:
                raise AuditFailure(FailureType.MODEL_RESPONSE) from None
            if self.cache is not None:
                historical = Usage(sum(usage.input_tokens for usage in attempts_usage),
                    sum(usage.output_tokens for usage in attempts_usage),
                    None if any(usage.cost_microusd is None for usage in attempts_usage) else
                    sum(usage.cost_microusd for usage in attempts_usage))
                envelope = {"format_version": 2, "key": key, "provenance": metadata,
                    "response": value, "response_sha256": digest(value), "historical_usage": asdict(historical),
                    "attempt_usage": [asdict(usage) for usage in attempts_usage],
                    "created_at": datetime.now(timezone.utc).isoformat()}
                if len(canonical(envelope)) > self.limits.max_response_bytes * 4 + 65536:
                    raise AuditFailure(FailureType.CACHE)
                self.cache.write(key, envelope)
                # Creation usage is already in this run's live totals. A replay
                # of that entry must not also count it as historical creation.
                self.seen_cache_keys.add(key)
            return ValidatedResponse(value, metadata, digest(value), False)
        raise AuditFailure(FailureType.PROVIDER)

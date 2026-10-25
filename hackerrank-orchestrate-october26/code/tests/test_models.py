"""Only fake clients: no credentials, hosted provider or network calls."""
from __future__ import annotations

import base64
from dataclasses import replace
import hashlib
import io
import csv
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import unittest

import test_workflow as workflow
from test_workflow import AT, BEFORE, SECRET, fixture
from audit_agent import AuditAgent, AuditFailure, FailureType, default_tools
from audit_agent.contracts import (Artifact, ExtractionInput, IndexInput, InvestigationInput, LoadInput, timestamp)
from audit_agent.model_adapters import ModelIntentInterpreter, ScreenshotAdapter, validate_intent_assessment
from audit_agent.model_runtime import (Attempt, InferenceLimits, ModelReply, ModelRequest, ModelRuntime,
                                       ProcessRunner, Purpose, ResponseCache, Usage, default_prompts)
from audit_agent.model_schemas import canonical, digest

PNG = base64.b64decode("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+a+m0AAAAASUVORK5CYII=")
UNKNOWN = {"action": "unknown", "affirmed": False, "negated": False, "conditional": False, "spans": []}


class FakeRunner:
    def __init__(self, results):
        self.results = list(results)
        self.calls = []

    def run(self, client, request, timeout, maximum):
        self.calls.append(request)
        result = self.results.pop(0)
        if isinstance(result, BaseException):
            raise result
        return result(request) if callable(result) else result


class SleepingClient:
    def complete(self, request):
        time.sleep(3)
        return ModelReply("fake", "test-model", json.dumps(UNKNOWN), Usage(1, 1, 0))


class FixtureClient:
    def complete(self, request):
        return ModelReply("fake", "test-model", json.dumps(screen_response()), Usage(7, 3, 100))


def fake_client_factory():
    return FixtureClient()


def screen_response():
    return {"complete": True, "records": [{
        "system_text": "account_service", "resource_text": "account_alpha", "category_text": "USER_PROFILE",
        "result_text": "FOUND", "subject_text": "alpha@example.test", "observed_at_text": None,
        "visible_text": "account_service account_alpha USER_PROFILE FOUND alpha@example.test", "box": [0, 0, 1, 1]}]}


def reply(value=UNKNOWN, usage=Usage(7, 3, 100)):
    return Attempt(ModelReply("fake", "test-model", value if isinstance(value, str) else json.dumps(value), usage), usage)


class ModelTests(unittest.TestCase):
    setUp = workflow.WorkflowTests.setUp

    def runtime(self, results=(), *, allow_live=True, limits=None, cache=True, prompts=None, clock=None):
        runner = FakeRunner(results)
        runtime = ModelRuntime("fake", "test-model", client="fake-client", allow_live=allow_live,
            cache=ResponseCache(self.root / "cache") if cache else None, limits=limits,
            runner=runner, prompts=prompts, **({"clock": clock} if clock else {}))
        return runtime, runner

    def ask(self, runtime, validator=lambda value: None):
        return runtime.request(Purpose.INTENT, b"unclear request", "text/plain",
                               {"source_id": "fixture", "captured_at": AT}, validator)

    def cache_file(self):
        return next((self.root / "cache").glob("*.json"))

    def test_live_is_opt_in_even_with_a_client(self):
        runtime, runner = self.runtime([reply()], allow_live=False)
        with self.assertRaises(AuditFailure) as caught:
            self.ask(runtime)
        self.assertEqual(caught.exception.kind, FailureType.LIVE_DISABLED)
        self.assertEqual(runner.calls, [])

    def test_cache_hit_validated_without_live_and_does_not_rebill_historical_usage(self):
        runtime, runner = self.runtime([reply()])
        first = self.ask(runtime)
        cache_bytes = self.cache_file().read_bytes()
        self.ask(runtime)
        self.assertEqual(runtime.summary()["model_calls"], 1)
        self.assertEqual(runtime.summary()["cache_historical_input_tokens"], 0)
        offline, offline_runner = self.runtime(allow_live=False)
        second = self.ask(offline)
        self.assertEqual(first.value, second.value)
        self.assertTrue(second.cache_hit)
        self.assertEqual(offline.summary()["model_calls"], 0)
        self.assertEqual(offline.summary()["input_tokens"], 0)
        self.assertEqual(offline.summary()["cache_historical_input_tokens"], 7)
        self.ask(offline)
        self.assertEqual(offline.summary()["cache_hits"], 2)
        self.assertEqual(offline.summary()["cache_historical_input_tokens"], 7)
        self.assertEqual(offline.summary()["cache_historical_model_calls"], 1)
        self.assertEqual(self.cache_file().read_bytes(), cache_bytes)
        self.assertEqual(offline_runner.calls, [])

    def test_malformed_live_json_is_metered_and_never_cached(self):
        runtime, _ = self.runtime([reply("not JSON " + SECRET)])
        with self.assertRaises(AuditFailure) as caught:
            self.ask(runtime)
        self.assertEqual(caught.exception.kind, FailureType.MODEL_RESPONSE)
        self.assertEqual(runtime.summary()["total_tokens"], 10)
        self.assertFalse((self.root / "cache").exists())
        self.assertNotIn(SECRET, json.dumps(runtime.summary()))

    def test_extra_properties_duplicate_keys_nan_and_wrong_types_are_rejected(self):
        bad = [dict(UNKNOWN, deletion_status="COMPLETE"), {**UNKNOWN, "affirmed": 1},
               '{"action":"unknown","action":"export","affirmed":false,"negated":false,"conditional":false,"spans":[]}',
               '{"action":"unknown","affirmed":NaN,"negated":false,"conditional":false,"spans":[]}']
        for value in bad:
            with self.subTest(value=str(value)[:30]):
                runtime, runner = self.runtime([reply(value)], cache=False)
                with self.assertRaises(AuditFailure) as caught:
                    self.ask(runtime)
                self.assertEqual(caught.exception.kind, FailureType.MODEL_RESPONSE)
                self.assertEqual(len(runner.calls), 1)  # No schema-repair retry loop.

    def test_corrupt_cache_is_not_repaired_by_live_fallback(self):
        runtime, _ = self.runtime([reply()]); self.ask(runtime)
        path = self.cache_file(); path.write_text("corrupt " + SECRET, encoding="utf-8")
        next_runtime, runner = self.runtime([reply()])
        with self.assertRaises(AuditFailure) as caught:
            self.ask(next_runtime)
        self.assertEqual(caught.exception.kind, FailureType.CACHE)
        self.assertEqual(runner.calls, [])
        self.assertIn(SECRET, path.read_text())  # History is not overwritten.

    def test_cache_hash_binding_schema_and_usage_are_rechecked(self):
        runtime, _ = self.runtime([reply()]); self.ask(runtime)
        path = self.cache_file(); original = path.read_bytes()
        mutations = [lambda d: d.update(response_sha256="0"*64),
                     lambda d: d["provenance"]["binding"].update(source_id="another"),
                     lambda d: d["historical_usage"].update(input_tokens=True),
                     lambda d: d.update(response={**UNKNOWN, "evidence_id": "invented"})]
        for mutate in mutations:
            data = json.loads(original); mutate(data)
            if "evidence_id" in data["response"]:
                data["response_sha256"] = digest(data["response"])
            path.write_bytes(canonical(data))
            offline, _ = self.runtime(allow_live=False)
            with self.assertRaises(AuditFailure) as caught:
                self.ask(offline)
            self.assertEqual(caught.exception.kind, FailureType.CACHE)
        path.write_bytes(original)

    def test_cache_semantics_are_rechecked_even_with_valid_schema_and_digest(self):
        runtime, _ = self.runtime([reply()]); self.ask(runtime)
        offline, _ = self.runtime(allow_live=False)
        def reject(value):
            raise ValueError(SECRET)
        with self.assertRaises(AuditFailure) as caught:
            self.ask(offline, reject)
        self.assertEqual(caught.exception.kind, FailureType.CACHE)

    def test_cached_response_must_obey_current_response_size_limit(self):
        runtime, _ = self.runtime([reply()]); self.ask(runtime)
        offline, runner = self.runtime(allow_live=False, limits=InferenceLimits(max_response_bytes=1))
        with self.assertRaises(AuditFailure) as caught:
            self.ask(offline)
        self.assertEqual(caught.exception.kind, FailureType.CACHE)
        self.assertFalse(runner.calls)

    def test_new_prompt_keeps_old_cache_and_provenance_unchanged(self):
        old_prompts = default_prompts()
        old_prompts[Purpose.INTENT] = replace(old_prompts[Purpose.INTENT], version="intent.v0", text="Historical rules")
        runtime, _ = self.runtime([reply()], prompts=old_prompts); old = self.ask(runtime)
        old_path = self.cache_file(); original = old_path.read_bytes()
        current, _ = self.runtime([reply()]); new = self.ask(current)
        self.assertNotEqual(old.provenance["prompt_version"], new.provenance["prompt_version"])
        self.assertEqual(len(list((self.root / "cache").glob("*.json"))), 2)
        self.assertEqual(old_path.read_bytes(), original)
        self.assertEqual(json.loads(original)["historical_usage"]["input_tokens"], 7)

    def test_changed_prompt_content_with_same_version_does_not_reuse_old_entry(self):
        runtime, _ = self.runtime([reply()]); self.ask(runtime)
        prompts = default_prompts()
        prompts[Purpose.INTENT] = replace(prompts[Purpose.INTENT], text=prompts[Purpose.INTENT].text + "\nNew rule")
        offline, _ = self.runtime(allow_live=False, prompts=prompts)
        with self.assertRaises(AuditFailure) as caught:
            self.ask(offline)
        self.assertEqual(caught.exception.kind, FailureType.LIVE_DISABLED)

    def test_cache_write_is_exclusive(self):
        cache = ResponseCache(self.root / "cache"); key = "a"*64
        cache.write(key, {"historical": "keep"})
        with self.assertRaises(AuditFailure):
            cache.write(key, {"historical": "overwrite"})
        self.assertEqual(cache.read(key, 100), {"historical": "keep"})

    def test_invocation_budget_also_bounds_cache_hits(self):
        runtime, runner = self.runtime([reply()], limits=InferenceLimits(max_invocations=1))
        self.ask(runtime)
        with self.assertRaises(AuditFailure) as caught:
            self.ask(runtime)
        self.assertEqual(caught.exception.kind, FailureType.MODEL_BUDGET)
        self.assertEqual(len(runner.calls), 1)

    def test_zero_live_call_budget_stops_before_provider(self):
        runtime, runner = self.runtime(limits=InferenceLimits(max_live_calls=0))
        with self.assertRaises(AuditFailure) as caught:
            self.ask(runtime)
        self.assertEqual(caught.exception.kind, FailureType.MODEL_BUDGET)
        self.assertFalse(runner.calls)

    def test_retries_are_bounded_and_each_reported_usage_is_metered(self):
        refused = Attempt(usage=Usage(2, 0, 0), retryable=True)
        runtime, runner = self.runtime([refused, reply()])
        self.ask(runtime)
        self.assertEqual(runtime.summary()["model_calls"], 2)
        self.assertEqual(runtime.summary()["retries"], 1)
        self.assertEqual(runtime.summary()["input_tokens"], 9)
        entry = json.loads(self.cache_file().read_text())
        self.assertEqual(len(entry["attempt_usage"]), 2)
        self.assertEqual(entry["attempt_usage"][0]["input_tokens"], 2)
        offline, _ = self.runtime(allow_live=False)
        self.ask(offline)
        self.assertEqual(offline.summary()["cache_historical_input_tokens"], 9)
        self.assertEqual(offline.summary()["cache_historical_model_calls"], 2)
        self.assertEqual(offline.summary()["model_calls"], 0)
        exhausted, second = self.runtime([refused, refused, reply()], cache=False)
        with self.assertRaises(AuditFailure) as caught:
            self.ask(exhausted)
        self.assertEqual(caught.exception.kind, FailureType.PROVIDER)
        self.assertEqual(len(second.calls), 2)

    def test_unknown_usage_stops_retry_and_is_never_reported_as_free(self):
        runtime, runner = self.runtime([Attempt(retryable=True), reply()])
        with self.assertRaises(AuditFailure) as caught:
            self.ask(runtime)
        self.assertEqual(caught.exception.kind, FailureType.MODEL_USAGE)
        self.assertEqual(len(runner.calls), 1)
        self.assertFalse(runtime.summary()["usage_complete"])
        self.assertIsNone(runtime.summary()["cost_microusd"])

    def test_timeout_is_non_retryable_with_unknown_billing(self):
        runtime, runner = self.runtime([TimeoutError(), reply()])
        with self.assertRaises(AuditFailure) as caught:
            self.ask(runtime)
        self.assertEqual(caught.exception.kind, FailureType.MODEL_TIMEOUT)
        self.assertEqual(len(runner.calls), 1)
        self.assertEqual(runtime.summary()["unmetered_attempts"], 1)

    def test_real_worker_can_be_terminated_without_waiting_for_slow_fake_client(self):
        request = ModelRequest(Purpose.INTENT, "prompt", {}, b"text", "text/plain", 10, 0.05)
        started = time.perf_counter()
        with self.assertRaises(TimeoutError):
            ProcessRunner().run(SleepingClient(), request, 0.05, 1024)
        self.assertLess(time.perf_counter() - started, 2.5)

    def test_actual_tokens_over_budget_are_counted_before_abort(self):
        runtime, _ = self.runtime([reply(usage=Usage(7, 3, 100))], limits=InferenceLimits(max_total_tokens=9))
        with self.assertRaises(AuditFailure) as caught:
            self.ask(runtime)
        self.assertEqual(caught.exception.kind, FailureType.MODEL_BUDGET)
        self.assertEqual(runtime.summary()["total_tokens"], 10)
        self.assertFalse((self.root / "cache").exists())

    def test_output_token_cap_is_checked_against_reported_usage(self):
        runtime, _ = self.runtime([reply()], limits=InferenceLimits(max_output_tokens=2))
        with self.assertRaises(AuditFailure) as caught:
            self.ask(runtime)
        self.assertEqual(caught.exception.kind, FailureType.MODEL_BUDGET)

    def test_elapsed_run_budget_prevents_further_work(self):
        now = [0.0]
        runtime, runner = self.runtime(clock=lambda: now[0], limits=InferenceLimits(total_seconds=1))
        now[0] = 2
        with self.assertRaises(AuditFailure) as caught:
            self.ask(runtime)
        self.assertEqual(caught.exception.kind, FailureType.MODEL_BUDGET)
        self.assertFalse(runner.calls)

    def test_invalid_limits_and_unapproved_purpose_or_mime_are_rejected(self):
        for limits in [InferenceLimits(max_retries=3), InferenceLimits(timeout_seconds=float("inf")),
                       InferenceLimits(max_live_calls=-1), InferenceLimits(max_invocations=True)]:
            with self.assertRaises(AuditFailure):
                self.runtime(limits=limits)
        with self.assertRaises(AuditFailure):
            self.runtime(allow_live="false")
        runtime, _ = self.runtime()
        with self.assertRaises(AuditFailure):
            runtime.request("remediation", b"data", "text/plain", {}, lambda v: None)
        with self.assertRaises(AuditFailure):
            runtime.request(Purpose.SCREENSHOT, b"PDF document", "application/pdf", {}, lambda v: None)

    def test_wrong_reported_provider_model_is_not_silently_attributed(self):
        attempt = reply(); attempt = replace(attempt, reply=replace(attempt.reply, model="other-model"))
        runtime, _ = self.runtime([attempt])
        with self.assertRaises(AuditFailure):
            self.ask(runtime)
        self.assertFalse(runtime.summary()["usage_complete"])
        self.assertEqual(runtime.summary()["identity_mismatches"], 1)

    def screenshot_fixture(self):
        config = fixture(self.root, extra_artifact=True)
        (config.dataset / "evidence/needs-ocr.png").write_bytes(PNG)
        tools = default_tools(); loaded = tools.load(LoadInput(config))
        native = tools.extract(ExtractionInput(replace(loaded, artifacts=loaded.artifacts[:1]), config.max_observations))
        return config, loaded, loaded.artifacts[1], native.observations

    def screen_response(self):
        return screen_response()

    def test_screenshot_facts_are_bound_in_code_not_by_model(self):
        _, loaded, image, facts = self.screenshot_fixture()
        runtime, runner = self.runtime([reply(self.screen_response())])
        packet = ScreenshotAdapter(runtime).extract(image, loaded, facts)
        observation = packet.observations[0]
        self.assertEqual(observation.source_id, image.file_id)
        self.assertEqual(observation.captured_at, image.captured_at)
        self.assertEqual(observation.model_provenance.content_sha256, hashlib.sha256(PNG).hexdigest())
        self.assertEqual(observation.model_provenance.prompt_version, "screenshot.v1")
        self.assertEqual(runner.calls[0].purpose, Purpose.SCREENSHOT)
        self.assertIn("untrusted", runner.calls[0].system_prompt)
        self.assertNotIn(image.file_id, runner.calls[0].system_prompt)

    def test_screenshot_invented_ids_citations_commands_boxes_and_unquoted_fields_fail(self):
        _, loaded, image, facts = self.screenshot_fixture()
        for kind in ("id", "citation", "command", "box", "quote", "partial"):
            value = self.screen_response()
            row = value["records"][0]
            if kind == "id":
                row["resource_text"] = "invented_resource"; row["visible_text"] += " invented_resource"
            elif kind == "citation":
                row["evidence_id"] = "chosen-by-model"
            elif kind == "command":
                value["remediation"] = "DELETE_RECORD"
            elif kind == "box":
                row["box"] = [0, 0, 2, 1]
            elif kind == "quote":
                row["subject_text"] = "not-visible@example.test"
            else:
                value["complete"] = False
            runtime, _ = self.runtime([reply(value)], cache=False)
            with self.subTest(kind=kind), self.assertRaises(AuditFailure) as caught:
                ScreenshotAdapter(runtime).extract(image, loaded, facts)
            self.assertEqual(caught.exception.kind, FailureType.MODEL_RESPONSE)

    def test_cached_screenshot_is_rebound_and_semantically_revalidated(self):
        _, loaded, image, facts = self.screenshot_fixture()
        runtime, _ = self.runtime([reply(self.screen_response())])
        ScreenshotAdapter(runtime).extract(image, loaded, facts)
        path = self.cache_file(); entry = json.loads(path.read_text())
        row = entry["response"]["records"][0]; row["resource_text"] = "invented_resource"
        row["visible_text"] += " invented_resource"; entry["response_sha256"] = digest(entry["response"])
        path.write_bytes(canonical(entry))
        offline, runner = self.runtime(allow_live=False)
        with self.assertRaises(AuditFailure) as caught:
            ScreenshotAdapter(offline).extract(image, loaded, facts)
        self.assertEqual(caught.exception.kind, FailureType.CACHE)
        self.assertEqual(runner.calls, [])

    def test_models_never_receive_non_screenshot_evidence(self):
        _, loaded, image, facts = self.screenshot_fixture()
        runtime, runner = self.runtime()
        with self.assertRaises(AuditFailure) as caught:
            ScreenshotAdapter(runtime).extract(replace(image, suffix=".sql"), loaded, facts)
        self.assertEqual(caught.exception.kind, FailureType.UNSUPPORTED)
        self.assertFalse(runner.calls)

    def test_known_intent_never_calls_model_and_ambiguous_intent_uses_exact_spans(self):
        config = fixture(self.root)
        loaded = default_tools().load(LoadInput(config)); request = loaded.requests[0]
        runtime, runner = self.runtime()
        with self.assertRaises(AuditFailure):
            ModelIntentInterpreter(runtime).interpret(request)
        self.assertEqual(runner.calls, [])
        ambiguous = replace(request, request_text="I need my profile gone for good.")
        value = {"action": "delete_account", "affirmed": True, "negated": False, "conditional": False,
                 "spans": [{"start": 0, "end": len(ambiguous.request_text), "text": ambiguous.request_text}]}
        runtime, _ = self.runtime([reply(value)])
        assessment = ModelIntentInterpreter(runtime).interpret(ambiguous)
        self.assertEqual(assessment.source_id, request.case_id)
        self.assertEqual(assessment.message_sha256, hashlib.sha256(ambiguous.request_text.encode()).hexdigest())
        with self.assertRaises(ValueError):
            validate_intent_assessment(ambiguous, replace(assessment, action="export"))

    def test_intent_fabricated_spans_and_conditional_authorization_fail(self):
        config = fixture(self.root); request = default_tools().load(LoadInput(config)).requests[0]
        request = replace(request, request_text="I need my profile gone for good.")
        base = {"action": "delete_account", "affirmed": True, "negated": False, "conditional": False,
                "spans": [{"start": 0, "end": len(request.request_text), "text": request.request_text}]}
        for change in ("span", "conditional", "negation", "citation"):
            value = json.loads(json.dumps(base))
            if change == "span": value["spans"][0]["text"] = "fabricated"
            elif change == "conditional": value["conditional"] = True
            elif change == "negation": value["negated"] = True
            else: value["evidence_id"] = "invented"
            runtime, _ = self.runtime([reply(value)], cache=False)
            with self.subTest(change=change), self.assertRaises(AuditFailure):
                ModelIntentInterpreter(runtime).interpret(request)

    def test_budget_exhaustion_in_real_pipeline_preserves_previous_output_and_logs_usage_only(self):
        config, _, _, _ = self.screenshot_fixture()
        runtime, _ = self.runtime([reply(self.screen_response())], limits=InferenceLimits(max_total_tokens=1))
        config.output.write_bytes(b"previous")
        with self.assertRaises(AuditFailure) as caught:
            AuditAgent(default_tools(model_runtime=runtime), self.telemetry).run(config)
        self.assertEqual(caught.exception.kind, FailureType.MODEL_BUDGET)
        self.assertEqual(config.output.read_bytes(), b"previous")
        serialized = json.dumps(self.events)
        self.assertNotIn("alpha@example.test", serialized)
        self.assertNotIn("visible_text", serialized)
        self.assertEqual(self.events[-1]["inference_usage"]["total_tokens"], 10)

    def test_screenshot_pipeline_and_cache_only_replay_preserve_prediction_bytes(self):
        config, _, _, _ = self.screenshot_fixture()
        runtime, _ = self.runtime([reply(self.screen_response())])
        AuditAgent(default_tools(model_runtime=runtime)).run(config)
        first = config.output.read_bytes()
        offline, runner = self.runtime(allow_live=False)
        AuditAgent(default_tools(model_runtime=offline)).run(config)
        self.assertEqual(config.output.read_bytes(), first)
        self.assertFalse(runner.calls)
        self.assertEqual(offline.summary()["cache_hits"], 1)

    def test_cli_requires_explicit_profile_and_live_client_configuration(self):
        config = fixture(self.root); cli = Path(__file__).resolve().parents[1] / "main.py"
        result = subprocess.run([sys.executable, "-B", str(cli), "--dataset", str(config.dataset),
            "--output", str(config.output), "--telemetry", str(self.root / "telemetry.jsonl"),
            "--expected-cases", "3", "--allow-live"], capture_output=True, text=True)
        self.assertEqual(result.returncode, 1)
        self.assertEqual(json.loads(result.stderr)["failure_type"], "input_invalid")
        self.assertFalse(config.output.exists())

    def test_cli_live_fake_client_then_cache_only_replay(self):
        config, _, _, _ = self.screenshot_fixture()
        cli = Path(__file__).resolve().parents[1] / "main.py"
        command = [sys.executable, "-B", str(cli), "--dataset", str(config.dataset), "--output", str(config.output),
            "--telemetry", str(self.root / "telemetry.jsonl"), "--expected-cases", "3",
            "--inference-provider", "fake", "--inference-model", "test-model", "--model-cache", str(self.root / "cache")]
        environment = {**os.environ, "PYTHONPATH": str(Path(__file__).resolve().parent)}
        live = subprocess.run([*command, "--allow-live", "--model-client", "test_models:fake_client_factory"],
                              env=environment, capture_output=True, text=True)
        self.assertEqual(live.returncode, 0, live.stderr)
        self.assertEqual(json.loads(live.stdout)["inference_usage"]["model_calls"], 1)
        first = config.output.read_bytes()
        offline = subprocess.run(command, env=environment, capture_output=True, text=True)
        self.assertEqual(offline.returncode, 0, offline.stderr)
        self.assertEqual(json.loads(offline.stdout)["inference_usage"]["model_calls"], 0)
        self.assertEqual(config.output.read_bytes(), first)

    def test_cli_client_presence_does_not_enable_live_calls(self):
        config, _, _, _ = self.screenshot_fixture()
        cli = Path(__file__).resolve().parents[1] / "main.py"
        result = subprocess.run([sys.executable, "-B", str(cli), "--dataset", str(config.dataset),
            "--output", str(config.output), "--telemetry", str(self.root / "telemetry.jsonl"), "--expected-cases", "3",
            "--inference-provider", "fake", "--inference-model", "test-model", "--model-cache", str(self.root / "cache"),
            "--model-client", "must_not_import_this:factory"], capture_output=True, text=True)
        self.assertEqual(result.returncode, 1)
        summary = json.loads(result.stderr)
        self.assertEqual(summary["failure_type"], "live_inference_disabled")
        self.assertEqual(summary["inference_usage"]["model_calls"], 0)
        self.assertNotIn("must_not_import_this", result.stderr)

    def test_ambiguous_intent_is_wired_through_pipeline_and_cached(self):
        config = fixture(self.root)
        path = config.dataset / "deletion_requests.csv"
        with path.open(encoding="utf-8", newline="") as stream:
            rows = list(csv.reader(stream))
        text = "I need my profile gone for good."
        rows[1][-1] = text
        with path.open("w", encoding="utf-8", newline="") as stream:
            csv.writer(stream).writerows(rows)
        value = {"action": "delete_account", "affirmed": True, "negated": False, "conditional": False,
                 "spans": [{"start": 0, "end": len(text), "text": text}]}
        runtime, _ = self.runtime([reply(value)])
        AuditAgent(default_tools(model_runtime=runtime)).run(config)
        first = config.output.read_bytes()
        offline, runner = self.runtime(allow_live=False)
        AuditAgent(default_tools(model_runtime=offline)).run(config)
        self.assertEqual(config.output.read_bytes(), first)
        self.assertFalse(runner.calls)

    def test_screenshot_hash_mismatch_is_rejected_before_model_call(self):
        _, loaded, image, facts = self.screenshot_fixture()
        runtime, runner = self.runtime()
        with self.assertRaises(AuditFailure) as caught:
            ScreenshotAdapter(runtime).extract(replace(image, sha256="0"*64), loaded, facts)
        self.assertEqual(caught.exception.kind, FailureType.MALFORMED)
        self.assertFalse(runner.calls)

    def test_cache_capture_time_change_is_a_miss_not_rebinding(self):
        _, loaded, image, facts = self.screenshot_fixture()
        runtime, _ = self.runtime([reply(self.screen_response())])
        ScreenshotAdapter(runtime).extract(image, loaded, facts)
        old = self.cache_file().read_bytes()
        offline, _ = self.runtime(allow_live=False)
        with self.assertRaises(AuditFailure) as caught:
            ScreenshotAdapter(offline).extract(replace(image, captured_at=timestamp("2026-05-03T00:00:00Z")), loaded, facts)
        self.assertEqual(caught.exception.kind, FailureType.LIVE_DISABLED)
        self.assertEqual(self.cache_file().read_bytes(), old)

    def test_global_call_budget_can_stop_a_retry(self):
        runtime, runner = self.runtime([Attempt(usage=Usage(1, 0, 0), retryable=True), reply()],
                                        limits=InferenceLimits(max_live_calls=1))
        with self.assertRaises(AuditFailure) as caught:
            self.ask(runtime)
        self.assertEqual(caught.exception.kind, FailureType.MODEL_BUDGET)
        self.assertEqual(len(runner.calls), 1)


if __name__ == "__main__":
    unittest.main()

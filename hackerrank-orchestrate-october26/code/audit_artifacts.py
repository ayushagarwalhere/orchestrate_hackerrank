"""Durable local artifacts and the immutable approval passed to publication.

This module has filesystem effects only. It cannot inspect evidence, invoke a
model, select an audit decision or execute any proposed remediation.
"""
from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path
import tempfile


def fingerprint(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def atomic_json(path: Path, value, *, default=None) -> None:
    """Readers see the previous complete JSON or the new complete JSON."""
    path = Path(path)
    content = json.dumps(value, default=default, ensure_ascii=False,
                         allow_nan=False, indent=2).encode('utf-8') + b'\n'
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, name = tempfile.mkstemp(prefix='.json-', suffix='.tmp', dir=path.parent)
    temporary = Path(name)
    try:
        with os.fdopen(descriptor, 'wb') as stream:
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


@dataclass(frozen=True)
class ValidatedCandidate:
    """Approval binds a specific staged file and digest to its validated rows."""
    path: Path
    sha256: str
    rows: int

    def matches(self, path: Path) -> bool:
        return self.path == Path(path).resolve() and self.sha256 == fingerprint(path)

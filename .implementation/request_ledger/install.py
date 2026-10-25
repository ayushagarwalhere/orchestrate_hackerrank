"""Task-local installer: reject concurrent edits instead of overwriting them."""
from pathlib import Path
import ast
import hashlib
import json

root = Path.cwd()
staging = Path(__file__).resolve().parent
record = staging / "installed_hashes.json"
hashes = json.loads(record.read_text())
for path in (staging / "code").rglob("*"):
    if not path.is_file():
        continue
    name = str(path.relative_to(staging)).replace("\\", "/")
    target, data = root / name, path.read_bytes()
    if path.suffix == ".py":
        ast.parse(data.decode("utf-8"))
    if target.exists() and target.read_bytes() == data:
        continue
    if target.exists() and hashlib.sha256(target.read_bytes()).hexdigest() != hashes.get(name):
        raise RuntimeError("Concurrent change: " + name)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(data)
    hashes[name] = hashlib.sha256(data).hexdigest()
record.write_text(json.dumps(hashes, indent=2))

"""Screenshot → image facts via a vision LLM (plan/phases/phase7.md §2.2).

    uv run python code/image_extract.py [--only evidence_04] [--force]

For each image in the evidence manifest without a facts file, ask the model for facts (prompt:
code/prompts/image_facts.md), keep only records that pass the schema rules of evidence/images.py, and write
code/llm_cache/image_facts/<file_id>.json. Answers are cached (llm.py), so re-runs cost nothing.
"""

import argparse
import json
import hashlib
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))

from evidence import activity, images  # noqa: E402
from evidence.common import files_under, load_manifest  # noqa: E402
from llm import default_llm  # noqa: E402

PROMPT_PATH = ROOT / "code" / "prompts" / "image_facts_v3.md"
MIME = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg"}


def prompt_and_version():
    text = PROMPT_PATH.read_text(encoding="utf-8")
    version = re.search(r"prompt_version: (\S+)", text).group(1)
    return text, version


def valid_answer(answer):
    """Validate the model response before it enters a cache or evidence ledger."""
    if not isinstance(answer, dict) or set(answer) != {"records"} or not isinstance(answer["records"], list):
        return False
    list_fields = ("labels", "emails", "phones", "user_ids", "references", "unknown_fields")
    fields = {"resource_id", "category", "state", *list_fields}
    for record in answer["records"]:
        if not isinstance(record, dict) or set(record) != fields:
            return False
        if not isinstance(record["resource_id"], str):
            return False
        if any(not isinstance(record[field], list) or any(not isinstance(value, str) for value in record[field])
               for field in list_fields):
            return False
        if record["category"] is not None and (not isinstance(record["category"], str)
                or record["category"] not in {category.value for category in images.Category}):
            return False
        if record["state"] is not None and (not isinstance(record["state"], str)
                or record["state"] not in {state.value for state in images.State}):
            return False
    return True


def extract(data_dir, llm, only=None, force=False, facts_dir=images.FACTS_DIR):
    """Write facts for every image that needs them. Returns {file_id: kept/total or reason}."""
    manifest = load_manifest(data_dir)
    links = activity.catalog_links(activity.load_activities(data_dir))
    prompt, version = prompt_and_version()
    facts_dir = Path(facts_dir)
    facts_dir.mkdir(parents=True, exist_ok=True)
    results = {}
    for ef in files_under(manifest, "images", set(MIME)):
        if only and ef.file_id not in only:
            continue
        out = images.facts_path(ef.file_id, facts_dir)
        if out.exists() and not force:
            results[ef.file_id] = "exists"
            continue
        answer = llm.generate_json("image_facts", prompt, version, [(ef.path.read_bytes(), MIME[ef.path.suffix])],
                                   validate=valid_answer)
        if answer is None:
            results[ef.file_id] = "no answer (no key and no cache entry, or the call failed)"
            continue
        if any(record["unknown_fields"] or record["state"] is None or record["category"] is None
               for record in answer["records"]):
            # Preserve uncertainty instead of letting a missing flag become
            # RESTORE_BLOCKED/REDACTED. Existing v2 facts are never relabeled v3.
            raise ValueError(f"{ef.file_id}: live extraction contains unresolved fields")
        kept = [r for r in answer["records"] if isinstance(r, dict) and images._record_observation(ef, r, links)]
        if len(kept) != len(answer["records"]):
            raise ValueError(f"{ef.file_id}: live extraction contains unresolved resource links")
        facts = {
            "file_id": ef.file_id,
            "model": llm.model,
            "prompt_version": version,
            "records": answer["records"],
            "source_sha256": hashlib.sha256(ef.path.read_bytes()).hexdigest(),
        }
        out.write_text(json.dumps(facts, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")
        results[ef.file_id] = f"{len(kept)}/{len(answer['records'])} records usable"
    return results


def main():
    parser = argparse.ArgumentParser(description="Extract screenshot facts with the configured vision model")
    parser.add_argument("--data", default=str(ROOT / "dataset"))
    parser.add_argument("--only", nargs="*", help="file ids to process")
    parser.add_argument("--force", action="store_true", help="re-extract even if a facts file exists")
    args = parser.parse_args()
    llm = default_llm()
    for file_id, result in extract(Path(args.data), llm, set(args.only) if args.only else None, args.force).items():
        print(f"{file_id}: {result}")
    for row in llm.meter.summary():
        print(row)


if __name__ == "__main__":
    main()

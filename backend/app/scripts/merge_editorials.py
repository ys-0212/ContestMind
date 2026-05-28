"""
Merges an external editorial dataset into problems.jsonl.

The external dataset must be a JSONL or JSON file where each record has:
  - problem_id  (e.g. "1234A")  OR  contest_id + index
  - editorial   (string — the editorial text)
  - statement   (optional string — problem statement text)

Usage (from backend/ directory):
    python -m app.scripts.merge_editorials --source path/to/external.jsonl

After running, re-build the vector index:
    python -m app.scripts.chunk_documents
    python -m app.scripts.build_vector_index
"""
import json
import logging
import argparse
from pathlib import Path

from app.core.config import settings

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
)
logger = logging.getLogger(__name__)


def load_external(path: Path) -> dict:
    """Load external data into a dict keyed by problem_id."""
    external = {}
    suffix = path.suffix.lower()

    if suffix == ".jsonl":
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                rec = json.loads(line)
                pid = _extract_pid(rec)
                if pid:
                    external[pid] = rec
    elif suffix == ".json":
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        items = data if isinstance(data, list) else data.values()
        for rec in items:
            pid = _extract_pid(rec)
            if pid:
                external[pid] = rec
    else:
        raise ValueError(f"Unsupported file format: {suffix}. Use .json or .jsonl")

    logger.info(f"Loaded {len(external)} records from external dataset")
    return external


def _extract_pid(rec: dict) -> str | None:
    """Try to get a normalized problem_id from a record."""
    if "problem_id" in rec:
        return str(rec["problem_id"]).strip()
    if "contestId" in rec and "index" in rec:
        return f"{rec['contestId']}{rec['index']}".strip()
    return None


def main():
    parser = argparse.ArgumentParser(description="Merge external editorial data into problems.jsonl")
    parser.add_argument("--source", required=True, help="Path to external editorial dataset (.json or .jsonl)")
    parser.add_argument(
        "--overwrite", action="store_true", default=False,
        help="Overwrite existing editorial/statement even if already present"
    )
    args = parser.parse_args()

    source_path = Path(args.source)
    if not source_path.exists():
        logger.error(f"Source file not found: {source_path}")
        return

    target_file = settings.PROCESSED_DATA_DIR / "problems.jsonl"
    if not target_file.exists():
        logger.error(f"problems.jsonl not found at {target_file}")
        return

    external = load_external(source_path)

    problems = []
    with open(target_file, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                problems.append(json.loads(line))

    logger.info(f"Loaded {len(problems)} problems from {target_file}")

    merged = 0
    for p in problems:
        pid = p.get("problem_id")
        if pid not in external:
            continue

        ext = external[pid]

        if "editorial" in ext and ext["editorial"]:
            if not p.get("editorial") or args.overwrite:
                p["editorial"] = ext["editorial"].strip()
                merged += 1

        if "statement" in ext and ext["statement"]:
            if not p.get("statement") or args.overwrite:
                p["statement"] = ext["statement"].strip()

    logger.info(f"Merged editorials into {merged} problems")

    # Write back
    tmp = target_file.with_suffix(".jsonl.tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        for p in problems:
            f.write(json.dumps(p) + "\n")
    tmp.replace(target_file)

    logger.info(f"Saved updated problems.jsonl")
    logger.info("Next: python -m app.scripts.chunk_documents && python -m app.scripts.build_vector_index")


if __name__ == "__main__":
    main()

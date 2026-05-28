"""
Scrapes problem statements from Codeforces and merges them into problems.jsonl.

Usage (from backend/ directory):
    python -m app.scripts.scrape_statements [--limit 500] [--skip-existing]

Rate limit: 1 request/second. Scraping 500 problems takes ~10 minutes.
Codeforces blocks aggressive scrapers — do NOT lower the sleep below 1.0s.
"""
import json
import time
import logging
import argparse
import re
from pathlib import Path
from typing import Optional

import requests
from bs4 import BeautifulSoup

from app.core.config import settings

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
)
logger = logging.getLogger(__name__)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}
REQUEST_DELAY = 1.2  # seconds between requests — do not lower
REQUEST_TIMEOUT = 10


def parse_problem_id(problem_id: str) -> tuple[str, str]:
    """Split '1234AB' into ('1234', 'AB')."""
    match = re.match(r"^(\d+)([A-Z]\d*)$", problem_id)
    if not match:
        raise ValueError(f"Cannot parse problem_id: {problem_id}")
    return match.group(1), match.group(2)


def scrape_statement(contest_id: str, index: str) -> Optional[str]:
    """
    Fetches and returns the plain-text problem statement for one problem.
    Returns None if the page is unavailable or parsing fails.
    """
    url = f"https://codeforces.com/problemset/problem/{contest_id}/{index}"
    try:
        resp = requests.get(url, headers=HEADERS, timeout=REQUEST_TIMEOUT)
        if resp.status_code == 403:
            logger.warning(f"403 Forbidden — Codeforces is rate-limiting. Sleeping 30s.")
            time.sleep(30)
            return None
        if resp.status_code != 200:
            logger.warning(f"HTTP {resp.status_code} for {url}")
            return None

        soup = BeautifulSoup(resp.text, "html.parser")
        statement_div = soup.find("div", class_="problem-statement")
        if not statement_div:
            logger.warning(f"No .problem-statement div found for {contest_id}/{index}")
            return None

        # Remove the title header (already stored separately)
        title_header = statement_div.find("div", class_="title")
        if title_header:
            title_header.decompose()

        # Get plain text, preserve paragraph breaks
        text = statement_div.get_text(separator="\n").strip()
        # Collapse excessive blank lines
        text = re.sub(r"\n{3,}", "\n\n", text)
        return text

    except requests.RequestException as e:
        logger.error(f"Request failed for {contest_id}/{index}: {e}")
        return None


def main():
    parser = argparse.ArgumentParser(description="Scrape Codeforces problem statements.")
    parser.add_argument(
        "--limit", type=int, default=500,
        help="Max number of problems to scrape (default: 500)"
    )
    parser.add_argument(
        "--skip-existing", action="store_true", default=True,
        help="Skip problems that already have a statement (default: True)"
    )
    parser.add_argument(
        "--min-rating", type=int, default=800,
        help="Only scrape problems at or above this rating (default: 800)"
    )
    parser.add_argument(
        "--max-rating", type=int, default=2000,
        help="Only scrape problems at or below this rating (default: 2000)"
    )
    args = parser.parse_args()

    input_file = settings.PROCESSED_DATA_DIR / "problems.jsonl"
    if not input_file.exists():
        logger.error(f"problems.jsonl not found at {input_file}")
        return

    # Load all problems into memory
    problems = []
    with open(input_file, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                problems.append(json.loads(line))

    logger.info(f"Loaded {len(problems)} problems from {input_file}")

    # Filter candidates: rated problems in range, optionally skip already-scraped
    candidates = []
    for p in problems:
        rating = p.get("rating")
        if rating is None:
            continue
        if not (args.min_rating <= rating <= args.max_rating):
            continue
        if args.skip_existing and p.get("statement") and p["statement"].strip():
            continue
        candidates.append(p)

    # Sort by solved count proxy: lower problem_id index = more popular
    candidates = candidates[: args.limit]
    logger.info(
        f"Will scrape {len(candidates)} problems "
        f"(rating {args.min_rating}–{args.max_rating}, limit {args.limit})"
    )

    # Build an index for fast update
    problems_by_id = {p["problem_id"]: p for p in problems}

    scraped = 0
    failed = 0

    for i, problem in enumerate(candidates):
        pid = problem["problem_id"]
        try:
            contest_id, index = parse_problem_id(pid)
        except ValueError as e:
            logger.warning(str(e))
            failed += 1
            continue

        logger.info(f"[{i+1}/{len(candidates)}] Scraping {pid} ({problem.get('title', '')})")
        statement = scrape_statement(contest_id, index)

        if statement:
            problems_by_id[pid]["statement"] = statement
            scraped += 1
            logger.info(f"  Got {len(statement)} chars")
        else:
            failed += 1
            logger.warning(f"  Failed to scrape {pid}")

        time.sleep(REQUEST_DELAY)

        # Save checkpoint every 50 problems
        if (i + 1) % 50 == 0:
            _save(problems_by_id, input_file)
            logger.info(f"Checkpoint saved. Scraped {scraped}, failed {failed} so far.")

    # Final save
    _save(problems_by_id, input_file)
    logger.info(f"Done. Scraped: {scraped}, Failed: {failed}, Total in file: {len(problems_by_id)}")
    logger.info("Next step: re-run chunk_documents.py and build_vector_index.py")


def _save(problems_by_id: dict, output_file: Path):
    tmp = output_file.with_suffix(".jsonl.tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        for p in problems_by_id.values():
            f.write(json.dumps(p) + "\n")
    tmp.replace(output_file)


if __name__ == "__main__":
    main()

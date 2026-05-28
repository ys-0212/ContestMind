"""
Scrapes Codeforces editorial blog posts and merges per-problem sections into problems.jsonl.

How it works:
  1. Reads unique contest IDs from problems.jsonl
  2. Fetches https://codeforces.com/contest/{contestId} to find the editorial blog link
  3. Fetches the editorial blog post and splits it into per-problem sections
  4. Maps sections back to problem IDs and updates problems.jsonl

Coverage expectation:
  - Div 1/2/3/4 rated rounds: ~65-75% coverage
  - Gym, very old rounds (pre-2013): likely no editorial link found

Usage (from backend/ directory):
    python -m app.scripts.scrape_editorials [--limit 500]

Rate limit: 1 request/second. Scraping 1000 contests takes ~30 minutes.
"""
import json
import re
import time
import logging
import argparse
from pathlib import Path
from typing import Optional
from collections import defaultdict

import requests
from bs4 import BeautifulSoup, Tag

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
REQUEST_DELAY = 1.2
REQUEST_TIMEOUT = 10

# Patterns that indicate an editorial link in the contest page sidebar
EDITORIAL_KEYWORDS = ["editorial", "tutorial", "разбор", "решени"]


def fetch(url: str) -> Optional[BeautifulSoup]:
    """Fetch a URL and return a BeautifulSoup object, or None on failure."""
    try:
        resp = requests.get(url, headers=HEADERS, timeout=REQUEST_TIMEOUT)
        if resp.status_code == 403:
            logger.warning("403 Forbidden — rate limited. Sleeping 30s.")
            time.sleep(30)
            return None
        if resp.status_code != 200:
            logger.warning(f"HTTP {resp.status_code} for {url}")
            return None
        return BeautifulSoup(resp.text, "html.parser")
    except requests.RequestException as e:
        logger.error(f"Request failed for {url}: {e}")
        return None


def find_editorial_url(contest_id: str) -> Optional[str]:
    """
    Scrape the contest page and look for a link to the editorial blog post.
    Returns the full editorial URL, or None if not found.
    """
    contest_url = f"https://codeforces.com/contest/{contest_id}"
    soup = fetch(contest_url)
    if not soup:
        return None
    time.sleep(REQUEST_DELAY)

    # Look in the sidebar links and any anchors on the page
    for a in soup.find_all("a", href=True):
        href: str = a["href"]
        text: str = a.get_text(strip=True).lower()
        if any(kw in text for kw in EDITORIAL_KEYWORDS) or \
           any(kw in href.lower() for kw in EDITORIAL_KEYWORDS):
            if "/blog/entry/" in href:
                if href.startswith("http"):
                    return href
                return "https://codeforces.com" + href

    return None


def _elements_to_text(elements: list) -> str:
    """
    Extract clean text from a list of HTML elements.
    Spoiler content (display:none) is included — we want all editorial text.
    """
    parts = []
    for elem in elements:
        if not isinstance(elem, Tag):
            continue
        # Remove display:none so get_text captures spoiler content
        for hidden in elem.find_all(style=re.compile(r"display\s*:\s*none")):
            del hidden["style"]
        text = elem.get_text(separator="\n").strip()
        if text:
            parts.append(text)
    combined = "\n\n".join(parts)
    return re.sub(r"\n{3,}", "\n\n", combined).strip()


def parse_editorial_sections(soup: BeautifulSoup, contest_id: str, indices: list[str]) -> dict[str, str]:
    """
    Parse a Codeforces editorial blog post into per-problem sections.

    Modern CF editorials use:
      <h1><a href="/contest/{contestId}/problem/{index}">Title</a></h1>
    as section boundaries inside <div class="ttypography">.

    Fallback for older editorials:
      <h1> / <h2> / <h3> whose full text is just a letter+dot, e.g. "A." or "Problem B"
    """
    content_div = soup.find("div", class_="ttypography") or soup.find("div", class_="content")
    if not content_div:
        return {}

    indices_upper = {idx.upper() for idx in indices}
    # Matches /contest/123/problem/A in both relative and absolute URLs
    link_re = re.compile(r"/contest/\d+/problem/([A-H][1-9]?)", re.IGNORECASE)
    # Matches heading text like "A.", "Problem B", "C —", "D ▸ Title", "A►Title"
    heading_re = re.compile(
        r"^(?:problem\s+)?([A-H][1-9]?)[\.\s\-—▸►►▸]",
        re.IGNORECASE
    )

    result: dict[str, str] = {}
    current_index: Optional[str] = None
    current_elements: list = []

    def flush():
        nonlocal current_index, current_elements
        if current_index and current_elements:
            text = _elements_to_text(current_elements)
            if len(text) > 50:
                result[current_index] = text
        current_index = None
        current_elements = []

    def detect_problem_index(tag: Tag) -> Optional[str]:
        """Return the problem index (e.g. 'A', 'C1') if this tag is a section header."""
        # Strategy 1: link href contains /contest/.../problem/X
        link = tag.find("a", href=True)
        if link:
            m = link_re.search(link["href"])
            if m and m.group(1).upper() in indices_upper:
                return m.group(1).upper()

        # Strategy 2: short text starting with a problem letter
        text = tag.get_text(strip=True)
        if len(text) < 100:
            m = heading_re.match(text)
            if m and m.group(1).upper() in indices_upper:
                return m.group(1).upper()

        return None

    for child in content_div.children:
        if not isinstance(child, Tag):
            continue

        # Format 1: heading tags h1–h4 as section boundaries
        if child.name in ("h1", "h2", "h3", "h4"):
            idx = detect_problem_index(child)
            if idx:
                flush()
                current_index = idx
                continue

        # Format 2: top-level <div class="spoiler"> with problem letter in spoiler title
        elif child.name == "div" and "spoiler" in (child.get("class") or []):
            title_elem = (
                child.find("b", class_="spoiler-title")
                or child.find("div", class_="spoiler-title")
                or child.find("span", class_="spoiler-title")
            )
            if title_elem:
                idx = detect_problem_index(title_elem)
                if idx:
                    flush()
                    current_index = idx
                    current_elements.append(child)
                    continue

        # Format 3: short <p> whose primary content is a problem link
        # e.g. <p><a href="/contest/2215/problem/A">2215A - Title</a></p>
        elif child.name == "p" and len(child.get_text(strip=True)) < 120:
            idx = detect_problem_index(child)
            if idx:
                flush()
                current_index = idx
                continue

        if current_index is not None:
            current_elements.append(child)

    flush()
    return result


def _save(problems_by_id: dict, output_file: Path):
    tmp = output_file.with_suffix(".jsonl.tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        for p in problems_by_id.values():
            f.write(json.dumps(p) + "\n")
    tmp.replace(output_file)


def main():
    parser = argparse.ArgumentParser(description="Scrape Codeforces editorial blog posts.")
    parser.add_argument("--limit", type=int, default=2000,
                        help="Max number of contests to process (default: 2000)")
    parser.add_argument("--skip-existing", action=argparse.BooleanOptionalAction, default=True,
                        help="Skip problems that already have an editorial (default: True)")
    args = parser.parse_args()

    input_file = settings.PROCESSED_DATA_DIR / "problems.jsonl"
    if not input_file.exists():
        logger.error(f"problems.jsonl not found at {input_file}")
        return

    # Load all problems
    problems = []
    with open(input_file, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                problems.append(json.loads(line))

    logger.info(f"Loaded {len(problems)} problems.")

    # Group problems by contest ID, track indices per contest
    # problem_id = contestId + index (e.g. "1234A" → contest "1234", index "A")
    contest_to_problems: dict[str, list[dict]] = defaultdict(list)
    id_pattern = re.compile(r"^(\d+)([A-Z][1-9]?)$")

    problems_by_id = {p["problem_id"]: p for p in problems}

    for p in problems:
        pid = p["problem_id"]
        m = id_pattern.match(pid)
        if not m:
            continue
        contest_id, index = m.group(1), m.group(2)
        # Always register the contest so we don't miss partial coverage.
        # The skip check happens later when writing back results.
        contest_to_problems[contest_id].append(p)

    contests = list(contest_to_problems.keys())[:args.limit]
    logger.info(f"Will process {len(contests)} contests (limit={args.limit})")

    editorial_found = 0
    problems_updated = 0
    contests_no_editorial = 0
    for i, contest_id in enumerate(contests):
        contest_problems = contest_to_problems[contest_id]
        indices = [id_pattern.match(p["problem_id"]).group(2) for p in contest_problems
                if id_pattern.match(p["problem_id"])]

        logger.info(f"[{i+1}/{len(contests)}] Contest {contest_id} ({len(indices)} problems)")

        editorial_url = find_editorial_url(contest_id)
        if not editorial_url:
            logger.info(f"  No editorial link found for contest {contest_id}")
            contests_no_editorial += 1
        else:
            logger.info(f"  Editorial: {editorial_url}")
            editorial_found += 1

            soup = fetch(editorial_url)
            time.sleep(REQUEST_DELAY)

            if soup:
                sections = parse_editorial_sections(soup, contest_id, indices)
                for p in contest_problems:
                    m = id_pattern.match(p["problem_id"])
                    if not m:
                        continue
                    index = m.group(2).upper()
                    if index in sections:
                        existing = (problems_by_id[p["problem_id"]].get("editorial") or "").strip()
                        if args.skip_existing and existing:
                            logger.info(f"    {p['problem_id']}: already has editorial, skipping")
                            continue
                        problems_by_id[p["problem_id"]]["editorial"] = sections[index]
                        problems_updated += 1
                        logger.info(f"    {p['problem_id']}: {len(sections[index])} chars")
                    else:
                        logger.info(f"    {p['problem_id']}: section not found in blog")

        if (i + 1) % 25 == 0:
            _save(problems_by_id, input_file)
            logger.info(
                f"Checkpoint — editorials found: {editorial_found}, "
                f"problems updated: {problems_updated}, "
                f"no editorial: {contests_no_editorial}"
            )

        time.sleep(REQUEST_DELAY)

    _save(problems_by_id, input_file)
    logger.info("=" * 60)
    logger.info(f"Done.")
    logger.info(f"  Contests processed   : {len(contests)}")
    logger.info(f"  Editorial links found: {editorial_found}")
    logger.info(f"  Problems updated     : {problems_updated}")
    logger.info(f"  No editorial found   : {contests_no_editorial}")
    logger.info("Next: re-run chunk_documents → clear_vector_index → build_vector_index")


if __name__ == "__main__":
    main()

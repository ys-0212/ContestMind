import json
import logging
import random
import httpx
from typing import Optional, Dict, List

from app.core.config import settings
from app.schemas.problem import Problem, ProblemExample

logger = logging.getLogger(__name__)

CF_PROBLEMSET_URL = "https://codeforces.com/api/problemset.problems"
_SECTION_STOPS = {"Note", "Notes", "Scoring", "Interaction", "Explanation", "Example", "Examples"}


# ── Example parser ────────────────────────────────────────────────────────────

def _parse_examples(statement: Optional[str]) -> List[ProblemExample]:
    """
    Extract Input/Output example pairs from a scraped Codeforces statement.

    The scraper's `.get_text(separator="\\n")` produces sections like:
        …statement body…
        Input
        {example 1 input}
        Output
        {example 1 output}
        Input
        {example 2 input}
        …
    """
    if not statement:
        return []

    examples: List[ProblemExample] = []
    lines = statement.split("\n")
    i = 0

    while i < len(lines):
        if lines[i].strip() == "Input":
            i += 1
            input_lines: List[str] = []
            while i < len(lines) and lines[i].strip() != "Output":
                input_lines.append(lines[i])
                i += 1

            if i < len(lines) and lines[i].strip() == "Output":
                i += 1
                output_lines: List[str] = []
                while (
                    i < len(lines)
                    and lines[i].strip() != "Input"
                    and lines[i].strip() not in _SECTION_STOPS
                    and not lines[i].strip().lower().startswith("explanation")
                ):
                    output_lines.append(lines[i])
                    i += 1

                inp = "\n".join(input_lines).strip()
                out = "\n".join(output_lines).strip()
                if inp or out:
                    examples.append(ProblemExample(input=inp, output=out))
        else:
            i += 1

    return examples


# ── Service ───────────────────────────────────────────────────────────────────

class ProblemService:
    def __init__(self):
        self._problems_db: Dict[str, Problem] = {}
        self._cf_api_problems: Optional[List[dict]] = None
        self._cf_cache_file = settings.RAW_DATA_DIR / "codeforces" / "problemset_problems.json"
        self._load_scraped_problems()

    # ── Normalisation ─────────────────────────────────────────────────────────

    @staticmethod
    def _normalize(problem_id: str) -> str:
        return problem_id.strip().upper()

    # ── Scraped local DB ──────────────────────────────────────────────────────

    def _load_scraped_problems(self):
        input_file = settings.PROCESSED_DATA_DIR / "problems.jsonl"
        if not input_file.exists():
            logger.warning(
                f"problems.jsonl not found at {input_file}. "
                "Will fall back to Codeforces API cache for problem metadata."
            )
            return

        loaded = 0
        try:
            with open(input_file, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        data = json.loads(line)
                        problem = Problem(**data)
                        # Parse examples if not already stored
                        if not problem.examples and problem.statement:
                            problem = problem.model_copy(
                                update={
                                    "examples": _parse_examples(problem.statement),
                                    "has_statement": True,
                                }
                            )
                        else:
                            problem = problem.model_copy(
                                update={"has_statement": bool(problem.statement)}
                            )
                        self._problems_db[self._normalize(problem.problem_id)] = problem
                        loaded += 1
                    except Exception as e:
                        logger.warning(f"Skipping malformed problem line: {e}")
            logger.info(f"Loaded {loaded} scraped problems into memory index.")
        except Exception as e:
            logger.error(f"Error reading problems.jsonl: {e}", exc_info=True)

    # ── CF API cache ──────────────────────────────────────────────────────────

    def _get_cf_api_problems(self) -> List[dict]:
        """Return the CF API problemset list, caching in memory."""
        if self._cf_api_problems is not None:
            return self._cf_api_problems

        if self._cf_cache_file.exists():
            try:
                with open(self._cf_cache_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                problems = data.get("result", {}).get("problems", [])
                if problems:
                    self._cf_api_problems = problems
                    logger.info(f"Loaded {len(problems)} problems from CF API file cache.")
                    return self._cf_api_problems
            except Exception as e:
                logger.error(f"Failed to read CF cache: {e}")

        logger.info("Fetching Codeforces problemset from API…")
        try:
            with httpx.Client(timeout=30.0) as client:
                resp = client.get(CF_PROBLEMSET_URL)
                resp.raise_for_status()
                data = resp.json()
            problems = data.get("result", {}).get("problems", [])
            self._cf_cache_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self._cf_cache_file, "w", encoding="utf-8") as f:
                json.dump(data, f)
            logger.info(f"Fetched and cached {len(problems)} problems from CF API.")
            self._cf_api_problems = problems
        except Exception as e:
            logger.error(f"Failed to fetch CF problemset: {e}")
            self._cf_api_problems = []

        return self._cf_api_problems

    def _build_from_cf_api(self, normalized_id: str) -> Optional[Problem]:
        for p in self._get_cf_api_problems():
            contest_id = str(p.get("contestId", ""))
            index = str(p.get("index", ""))
            pid = self._normalize(f"{contest_id}{index}")
            if pid == normalized_id:
                return Problem(
                    problem_id=pid,
                    title=p.get("name", f"Problem {pid}"),
                    rating=p.get("rating"),
                    tags=p.get("tags", []),
                    url=f"https://codeforces.com/problemset/problem/{contest_id}/{index}",
                    statement=None,
                    editorial=None,
                    source="codeforces",
                    examples=[],
                    has_statement=False,
                )
        return None

    # ── Public API ────────────────────────────────────────────────────────────

    def get_problem(self, problem_id: str) -> Optional[Problem]:
        """
        Retrieve a problem by ID.
        Priority: local scraped DB (has statement) → CF API cache (metadata only).
        IDs are normalized to UPPERCASE before lookup.
        """
        normalized = self._normalize(problem_id)
        return self._problems_db.get(normalized) or self._build_from_cf_api(normalized)

    def get_all_problems(
        self,
        min_rating: int = 800,
        max_rating: int = 3500,
        limit: int = 1000,
        shuffle: bool = False,
    ) -> List[Problem]:
        """
        Return all known problems from both scraped DB and CF API cache.
        Used by recommendation and analytics services.
        Optionally filters by rating range and shuffles for random sampling.
        """
        seen: set = set()
        result: List[Problem] = []

        # 1. Scraped DB (highest quality — has statement/editorial)
        for problem in self._problems_db.values():
            if problem.rating and not (min_rating <= problem.rating <= max_rating):
                continue
            seen.add(problem.problem_id)
            result.append(problem)

        # 2. CF API cache (metadata only)
        for p in self._get_cf_api_problems():
            contest_id = str(p.get("contestId", ""))
            index = str(p.get("index", ""))
            pid = self._normalize(f"{contest_id}{index}")
            if pid in seen:
                continue
            rating = p.get("rating")
            if rating and not (min_rating <= rating <= max_rating):
                continue
            result.append(
                Problem(
                    problem_id=pid,
                    title=p.get("name", f"Problem {pid}"),
                    rating=rating,
                    tags=p.get("tags", []),
                    url=f"https://codeforces.com/problemset/problem/{contest_id}/{index}",
                    source="codeforces",
                    has_statement=False,
                )
            )
            seen.add(pid)

        if shuffle:
            random.shuffle(result)
        return result[:limit]

    def get_available_ids(self) -> List[str]:
        """Return all known problem IDs (scraped + CF cache)."""
        ids = set(self._problems_db.keys())
        for p in self._get_cf_api_problems():
            c = str(p.get("contestId", ""))
            i = str(p.get("index", ""))
            ids.add(self._normalize(f"{c}{i}"))
        return sorted(ids)

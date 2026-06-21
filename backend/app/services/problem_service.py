import json
import logging
import random
import httpx
from typing import Optional, Dict, List

from app.core.config import settings
from app.schemas.problem import Problem, ProblemExample
from supabase import Client

logger = logging.getLogger(__name__)

CF_PROBLEMSET_URL = "https://codeforces.com/api/problemset.problems"
_SECTION_STOPS = {"Note", "Notes", "Scoring", "Interaction", "Explanation", "Example", "Examples"}


# ── Example parser ────────────────────────────────────────────────────────────

def _parse_examples(statement: Optional[str]) -> List[ProblemExample]:
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
    def __init__(self, supabase_client: Optional[Client] = None):
        self.supabase_client = supabase_client
        self._problems_db: Dict[str, Problem] = {}
        self._cf_api_problems: Optional[List[dict]] = None
        self._cf_cache_file = settings.RAW_DATA_DIR / "codeforces" / "problemset_problems.json"
        
        # We only load JSONL if Supabase is not provided or it fails
        if not self.supabase_client:
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

    def _problem_from_supabase_row(self, row: dict) -> Problem:
        examples_data = row.get("examples")
        if isinstance(examples_data, str):
            examples_data = json.loads(examples_data)
        
        examples = [ProblemExample(**ex) for ex in (examples_data or [])]
        
        return Problem(
            problem_id=row.get("problem_id"),
            title=row.get("title", ""),
            rating=row.get("rating"),
            tags=row.get("tags") or [],
            url=row.get("url", ""),
            statement=row.get("statement"),
            editorial=row.get("editorial"),
            source=row.get("source", "codeforces"),
            examples=examples,
            has_statement=row.get("has_statement", False)
        )

    # ── Public API ────────────────────────────────────────────────────────────

    def get_problem(self, problem_id: str) -> Optional[Problem]:
        normalized = self._normalize(problem_id)
        
        problem = None
        if self.supabase_client:
            try:
                resp = self.supabase_client.table("problems").select("*").eq("problem_id", normalized).execute()
                if resp.data and len(resp.data) > 0:
                    problem = self._problem_from_supabase_row(resp.data[0])
            except Exception as e:
                logger.error(f"Supabase problem fetch failed: {e}")

        if not problem:
            problem = self._problems_db.get(normalized) or self._build_from_cf_api(normalized)
            
        if problem and not problem.statement:
            from app.services.scraper_service import ScraperService
            scraped = ScraperService.scrape_problem(normalized)
            if scraped:
                html_statement, examples = scraped
                problem = problem.model_copy(update={
                    "statement": html_statement,
                    "examples": [ProblemExample(**ex) for ex in examples],
                    "has_statement": True
                })
                # Cache it back to Supabase
                if self.supabase_client:
                    try:
                        self.supabase_client.table("problems").upsert({
                            "problem_id": problem.problem_id,
                            "title": problem.title,
                            "rating": problem.rating,
                            "tags": problem.tags,
                            "url": problem.url,
                            "statement": problem.statement,
                            "examples": examples,
                            "has_statement": True,
                            "source": "codeforces"
                        }).execute()
                    except Exception as e:
                        logger.error(f"Failed to cache scraped problem {normalized} to Supabase: {e}")
                
                # Update local DB if needed
                if normalized in self._problems_db:
                    self._problems_db[normalized] = problem
                    
        return problem

    def get_all_problems(
        self,
        min_rating: int = 800,
        max_rating: int = 3500,
        limit: int = 1000,
        shuffle: bool = False,
    ) -> List[Problem]:
        seen: set = set()
        result: List[Problem] = []

        if self.supabase_client:
            try:
                query = self.supabase_client.table("problems").select("*")
                if min_rating is not None:
                    query = query.gte("rating", min_rating)
                if max_rating is not None:
                    query = query.lte("rating", max_rating)
                
                # We fetch a larger pool and shuffle manually if needed, or just let Supabase return all matching
                resp = query.execute()
                for row in resp.data or []:
                    p = self._problem_from_supabase_row(row)
                    seen.add(p.problem_id)
                    result.append(p)
            except Exception as e:
                logger.error(f"Supabase problems fetch failed: {e}")
                # Fall through to local logic

        # Fallback to local DB
        if not self.supabase_client or not result:
            for problem in self._problems_db.values():
                if problem.rating and not (min_rating <= problem.rating <= max_rating):
                    continue
                seen.add(problem.problem_id)
                result.append(problem)

        # CF API cache (metadata only)
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
        ids = set()
        if self.supabase_client:
            try:
                resp = self.supabase_client.table("problems").select("problem_id").execute()
                ids.update([row["problem_id"] for row in resp.data])
            except Exception as e:
                pass

        ids.update(self._problems_db.keys())
        for p in self._get_cf_api_problems():
            c = str(p.get("contestId", ""))
            i = str(p.get("index", ""))
            ids.add(self._normalize(f"{c}{i}"))
        return sorted(ids)

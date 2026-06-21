import re
import logging
from fastapi import APIRouter, Depends, HTTPException, Query

from app.schemas.problem import Problem
from app.services.problem_service import ProblemService
from app.services.codeforces_service import CodeforcesService
from app.api.deps import get_problem_service, get_codeforces_service

logger = logging.getLogger(__name__)
router = APIRouter()


def _cf_url(problem_id: str) -> str:
    m = re.match(r"^(\d+)([A-Za-z][A-Za-z0-9]*)$", problem_id.strip())
    if m:
        return f"https://codeforces.com/problemset/problem/{m.group(1)}/{m.group(2).upper()}"
    return "https://codeforces.com/problemset"


@router.get("/available", response_model=dict)
def get_available_problems(
    min_rating: int = Query(800,  ge=0,    description="Minimum problem rating"),
    max_rating: int = Query(3500, le=5000, description="Maximum problem rating"),
    limit:      int = Query(15000,  ge=1, le=15000, description="Max problems to return"),
    problem_service: ProblemService = Depends(get_problem_service),
):
    """
    Returns all problems available in the local DB or CF API cache.
    Lightweight response — no statement text, only metadata.
    Filters by rating range and caps at `limit` (default 500).
    """
    problems = problem_service.get_all_problems(
        min_rating=min_rating,
        max_rating=max_rating,
        limit=limit,
        shuffle=False,
    )
    return {
        "problems": [
            {
                "problem_id": p.problem_id,
                "title":      p.title,
                "rating":     p.rating,
                "tags":       p.tags,
                "url":        p.url,
                "has_statement": p.has_statement,
            }
            for p in problems
        ],
        "count": len(problems),
    }


@router.get("", response_model=dict)
def get_all_problems(
    cf_service: CodeforcesService = Depends(get_codeforces_service),
):
    """Fetch the full Codeforces problemset (cached 24 h)."""
    problemset = cf_service.get_problemset()
    if not problemset:
        raise HTTPException(status_code=500, detail="Could not fetch problemset.")
    return problemset


@router.get("/{problem_id}", response_model=Problem)
def get_problem_details(
    problem_id: str,
    problem_service: ProblemService = Depends(get_problem_service),
):
    """
    Return full problem details.
    - Local scraped DB → full statement + editorial + parsed examples.
    - CF API cache     → metadata only (no statement/editorial).
    - Not found        → 404.
    """
    normalized = problem_id.strip().upper()
    logger.info(f"Problem detail request: '{problem_id}' → '{normalized}'")

    problem = problem_service.get_problem(normalized)
    if not problem:
        raise HTTPException(
            status_code=404,
            detail=f"Problem '{normalized}' not found in local DB or Codeforces API cache.",
        )
    return problem

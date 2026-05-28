# d:\Project\ContestMind\backend\app\scripts\preprocess_codeforces.py
import json
import logging
from typing import Any, Dict, List

from app.core.config import settings
from app.schemas.problem import Problem
from app.services.codeforces_service import CodeforcesService

# --- Basic Logging Setup ---
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
)
logger = logging.getLogger(__name__)


def normalize_problem(problem_data: Dict[str, Any]) -> Problem:
    problem_id = f"{problem_data['contestId']}{problem_data['index']}"
    return Problem(
        problem_id=problem_id,
        title=problem_data["name"],
        rating=problem_data.get("rating"),
        tags=problem_data.get("tags", []),
        url=f"https://codeforces.com/problemset/problem/{problem_data['contestId']}/{problem_data['index']}",
        source="codeforces",
    )


def main():
    logger.info("Starting Codeforces data ingestion and preprocessing pipeline...")
    service = CodeforcesService()
    raw_data = service.get_problemset()

    if not raw_data or raw_data.get("status") != "OK":
        logger.error("Failed to fetch data from Codeforces. Exiting.")
        return

    problems = raw_data.get("result", {}).get("problems", [])
    problem_stats = raw_data.get("result", {}).get("problemStatistics", [])
    ratings_map = {f"{p['contestId']}{p['index']}": p["rating"] for p in problems if "rating" in p}
    solved_map = {f"{p['contestId']}{p['index']}": p["solvedCount"] for p in problem_stats}

    processed_problems: List[Problem] = []
    for p_data in problems:
        p_id = f"{p_data['contestId']}{p_data['index']}"
        if p_id in ratings_map and p_id in solved_map and solved_map[p_id] > 0:
            p_data["rating"] = ratings_map[p_id]
            normalized = normalize_problem(p_data)
            processed_problems.append(normalized)

    logger.info(f"Successfully normalized {len(processed_problems)} problems.")

    output_dir = settings.PROCESSED_DATA_DIR
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / "problems.jsonl"

    try:
        with open(output_file, "w", encoding="utf-8") as f:
            for problem in processed_problems:
                f.write(problem.model_dump_json() + "\n")
        logger.info(f"Successfully saved processed data to {output_file}")
        logger.info(f"Total problems in dataset: {len(processed_problems)}")
    except IOError as e:
        logger.error(f"Error writing to file: {e}")

    logger.info("Pipeline finished successfully.")


if __name__ == "__main__":
    main()

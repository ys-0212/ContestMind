import json
import os
from collections import defaultdict
from pathlib import Path

# Paths relative to the script's execution context (assumes running from backend root or via absolute paths)
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
PROCESSED_FILE = PROJECT_ROOT / "data" / "processed" / "problems.jsonl"
REPORT_DIR = PROJECT_ROOT / "data" / "reports"
REPORT_FILE = REPORT_DIR / "editorial_coverage_report.json"

def analyze_coverage():
    if not PROCESSED_FILE.exists():
        print(f"Error: Processed dataset not found at {PROCESSED_FILE}")
        return

    total_problems = 0
    with_editorial = 0
    missing_editorial = 0
    editorial_lengths = []
    
    # Aggregation dictionaries
    contests_missing = defaultdict(int)
    rating_buckets = defaultdict(lambda: {"total": 0, "with_editorial": 0})
    
    print(f"Reading dataset from: {PROCESSED_FILE}")
    
    with open(PROCESSED_FILE, 'r', encoding='utf-8') as f:
        for line in f:
            if not line.strip():
                continue
                
            try:
                problem = json.loads(line)
            except json.JSONDecodeError:
                continue
                
            total_problems += 1
            
            # Extract metadata
            editorial = problem.get("editorial")
            
            problem_id = str(problem.get("problem_id", ""))
            import re
            match = re.match(r"^(\d+)", problem_id)
            contest_id = match.group(1) if match else "Unknown"
            
            rating = problem.get("rating", "Unrated")
            
            # Formatting rating bucket
            if isinstance(rating, (int, float)):
                bucket = f"{(rating // 100) * 100}-{(rating // 100) * 100 + 99}"
            else:
                bucket = str(rating)
                
            rating_buckets[bucket]["total"] += 1
            
            if editorial and len(editorial.strip()) > 10:  # Arbitrary threshold to ignore empty/stub strings
                with_editorial += 1
                rating_buckets[bucket]["with_editorial"] += 1
                editorial_lengths.append(len(editorial))
            else:
                missing_editorial += 1
                contests_missing[contest_id] += 1
                
    if total_problems == 0:
        print("No problems found in dataset.")
        return
        
    coverage_percentage = (with_editorial / total_problems) * 100
    avg_editorial_length = sum(editorial_lengths) / len(editorial_lengths) if editorial_lengths else 0
    
    # Sorting stats
    sorted_missing_contests = sorted(contests_missing.items(), key=lambda x: x[1], reverse=True)
    sorted_rating_buckets = sorted(rating_buckets.items(), key=lambda x: str(x[0]))
    
    # --- Console Output ---
    print("\n==================================================")
    print("      EDITORIAL COVERAGE QUALITY ANALYSIS")
    print("==================================================")
    print(f"Total Problems Processed  : {total_problems}")
    print(f"Problems WITH Editorial   : {with_editorial}")
    print(f"Problems MISSING Editorial: {missing_editorial}")
    print(f"Overall Coverage %        : {coverage_percentage:.2f}%")
    print(f"Avg Editorial Length      : {avg_editorial_length:.0f} characters")
    
    print("\n==================================================")
    print("      COVERAGE BY RATING BUCKET")
    print("==================================================")
    for bucket, stats in sorted_rating_buckets:
        total = stats["total"]
        has_ed = stats["with_editorial"]
        cov = (has_ed / total) * 100 if total > 0 else 0
        print(f"[{bucket:>9}] : {has_ed:>5} / {total:>5}  ({cov:>6.2f}%)")
        
    print("\n==================================================")
    print("      TOP 10 CONTESTS MISSING EDITORIALS")
    print("==================================================")
    for contest, count in sorted_missing_contests[:10]:
        print(f"Contest {contest:<8} : {count} problems missing")

    # --- Save JSON Report ---
    report_data = {
        "summary": {
            "total_problems": total_problems,
            "with_editorial": with_editorial,
            "missing_editorial": missing_editorial,
            "coverage_percentage": round(coverage_percentage, 2),
            "avg_editorial_length": round(avg_editorial_length, 2)
        },
        "rating_distribution": {
            k: {
                "total": v["total"], 
                "with_editorial": v["with_editorial"], 
                "coverage_pct": round((v["with_editorial"]/v["total"])*100, 2) if v["total"] > 0 else 0
            } for k, v in rating_buckets.items()
        },
        "top_contests_missing_editorials": [{"contestId": k, "missing_count": v} for k, v in sorted_missing_contests[:50]]
    }
    
    os.makedirs(REPORT_DIR, exist_ok=True)
    with open(REPORT_FILE, 'w', encoding='utf-8') as f:
        json.dump(report_data, f, indent=4)
        
    print("\n==================================================")
    print(f"Detailed JSON report saved to:\n{REPORT_FILE}")
    print("==================================================")


if __name__ == "__main__":
    analyze_coverage()

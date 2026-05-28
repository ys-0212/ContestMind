import logging
from collections import defaultdict
from typing import List, Dict, Any, Optional
import time

from app.services.codeforces_service import CodeforcesService
from app.services.llm.base import BaseLLMService
from app.schemas.analytics import AnalyticsResponse, DifficultyDistribution
from app.core.utils import ttl_cache

logger = logging.getLogger(__name__)

class AnalyticsService:
    def __init__(self, codeforces_service: CodeforcesService, llm_service: BaseLLMService):
        self.codeforces_service = codeforces_service
        self.llm_service = llm_service

    @ttl_cache(ttl_seconds=3600)  # Cache for 1 hour
    def analyze_weaknesses(self, handle: str) -> AnalyticsResponse:
        user_info = self.codeforces_service.get_user_info(handle)
        if not user_info:
            raise ValueError(f"Could not retrieve info for handle: {handle}")

        status = self.codeforces_service.get_user_status(handle)
        if not status:
            raise ValueError(f"Could not retrieve status for handle: {handle}")

        solved_problems = []
        attempted_tags = set()
        failed_attempts = []
        for sub in status:
            prob = sub.get("problem", {})
            tags = prob.get("tags", [])
            for tag in tags:
                if tag and not tag.startswith("*"):
                    attempted_tags.add(tag)
            
            if sub.get("verdict") == "OK":
                solved_problems.append(prob)
            else:
                failed_attempts.append(prob)

        # Deduplicate solved problems
        unique_solved = {f"{p.get('contestId')}{p.get('index')}": p for p in solved_problems}.values()

        tag_counts = defaultdict(int)
        ratings = []
        difficulty_counts = defaultdict(int)

        for prob in unique_solved:
            for tag in prob.get("tags", []):
                if tag and not tag.startswith("*"):
                    tag_counts[tag] += 1
            if "rating" in prob:
                rating = prob["rating"]
                ratings.append(rating)
                range_bucket = f"{(rating // 100) * 100}-{(rating // 100) * 100 + 99}"
                difficulty_counts[range_bucket] += 1

        # Fix 1: Filter rare tags (threshold >= 10 solves to be considered a strong/weak area, unless all are low)
        meaningful_tags = {tag: count for tag, count in tag_counts.items() if count >= 5}
        if not meaningful_tags:
            meaningful_tags = tag_counts # fallback if user has very few solves
            
        sorted_tags = sorted(meaningful_tags.items(), key=lambda item: item[1], reverse=True)
        strongest_tags = [tag for tag, count in sorted_tags[:3]]
        
        # Weakest tags: tags that were attempted but have low count, or bottom of meaningful tags
        weakest_tags = [tag for tag, count in sorted_tags[-3:]] if len(sorted_tags) >= 3 else []

        avg_rating = int(sum(ratings) / len(ratings)) if ratings else 0
        max_rating = max(ratings) if ratings else 0
        
        # Fix 3: Comfort zone logic (use median or peak of difficulty distribution instead of raw avg)
        if ratings:
            sorted_ratings = sorted(ratings)
            median_rating = sorted_ratings[len(sorted_ratings) // 2]
            comfort_zone = f"{max(0, median_rating - 100)}-{median_rating + 100}"
        else:
            comfort_zone = "N/A"

        # Fix 4: Unsolved high-rating attempts
        unsolved_high_rating = []
        if ratings:
            threshold = avg_rating + 200
            for prob in failed_attempts:
                if "rating" in prob and prob["rating"] >= threshold:
                    pid = f"{prob.get('contestId')}{prob.get('index')}"
                    if pid not in {f"{p.get('contestId')}{p.get('index')}" for p in unique_solved}:
                        unsolved_high_rating.append(f"{pid} ({prob['rating']})")
            unsolved_high_rating = list(set(unsolved_high_rating))[:5] # Top 5 unique

        # Recent activity
        now = time.time()
        recent_subs = [s for s in status if now - s.get("creationTimeSeconds", 0) < 30 * 24 * 3600]
        if len(recent_subs) > 20:
            recent_activity = "High (Active in last 30 days)"
        elif len(recent_subs) > 0:
            recent_activity = "Moderate"
        else:
            recent_activity = "Low (Inactive recently)"

        # Difficulty distribution list
        dist_list = [DifficultyDistribution(rating_range=k, solved_count=v) for k, v in sorted(difficulty_counts.items())]

        # Fix 2: Contest participation summary using user.rating
        rating_history = self.codeforces_service.get_user_rating(handle)
        if rating_history is not None:
            contest_count = len(rating_history)
            participation_summary = f"Participated in {contest_count} rated contests."
        else:
            participation_summary = "Contest participation data unavailable."

        # Holistic Weakness Generation via LLM
        # Identify standard CF topics
        standard_tags = ["math", "greedy", "dp", "data structures", "brute force", "graphs", "sortings", "dfs and similar", "binary search", "trees", "strings", "number theory", "geometry", "combinatorics"]
        topics_unexplored = [t for t in standard_tags if tag_counts.get(t, 0) == 0]
        topics_explored = [t for t in standard_tags if tag_counts.get(t, 0) > 0]

        prompt = f"""
        Act as an elite competitive programming coach analyzing the complete profile of {handle}.
        Rating: {user_info.get('rating', 'Unrated')} (Max: {user_info.get('maxRating', 'Unrated')}).
        Comfort Zone: {comfort_zone}. Total unique solved: {len(unique_solved)}.
        
        Top tags solved (Strengths): {', '.join([f"{t}({tag_counts[t]})" for t in strongest_tags])}
        Least solved attempted tags: {', '.join([f"{t}({tag_counts[t]})" for t in weakest_tags])}
        Completely unexplored standard tags (Zero solves): {', '.join(topics_unexplored) if topics_unexplored else 'None'}
        
        Write 3 deep, highly personalized coaching insights (sentences) explaining their holistic weaknesses and major domain blind spots. 
        Focus heavily on how their ignored/unexplored topics (if any) or uneven distributions are holding them back from reaching their next rating tier.
        Output exactly one sentence per line. Do not number them.
        """
        
        holistic_insights = []
        try:
            llm_res = self.llm_service.generate_text(prompt)
            holistic_insights = [line.strip('- *1234567890.') for line in llm_res.split('\n') if len(line.strip()) > 10]
            if not holistic_insights:
                holistic_insights = ["Your profile shows an imbalance in tag distribution.", "Focus on practicing unexplored domains."]
        except Exception as e:
            logger.error(f"Failed to generate holistic insights: {e}")
            holistic_insights = ["Unable to generate holistic insights at this time."]

        return AnalyticsResponse(
            handle=handle,
            current_rating=user_info.get("rating"),
            max_rating=user_info.get("maxRating"),
            weakest_tags=weakest_tags,
            strongest_tags=strongest_tags,
            average_solved_rating=avg_rating,
            highest_solved_rating=max_rating,
            recent_activity_trend=recent_activity,
            rating_comfort_zone=comfort_zone,
            tag_solve_distribution=dict(tag_counts),
            topics_explored=topics_explored,
            topics_unexplored=topics_unexplored,
            difficulty_distribution=dist_list,
            contest_participation_summary=participation_summary,
            holistic_weakness_insights=holistic_insights,
            unsolved_high_rating_attempts=unsolved_high_rating
        )

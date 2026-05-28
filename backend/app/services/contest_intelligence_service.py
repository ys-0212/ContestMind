import logging
from collections import defaultdict
from typing import Optional, List, Dict
import time

from app.schemas.contest_intelligence import ContestPerformanceProfile
from app.services.codeforces_service import CodeforcesService
from app.services.llm.base import BaseLLMService
from app.core.utils import ttl_cache

logger = logging.getLogger(__name__)

class ContestIntelligenceService:
    def __init__(self, codeforces_service: CodeforcesService, llm_service: BaseLLMService):
        self.cf_service = codeforces_service
        self.llm_service = llm_service

    @ttl_cache(ttl_seconds=3600)
    def analyze_contest_performance(self, handle: str) -> Optional[ContestPerformanceProfile]:
        logger.info(f"Analyzing contest performance for {handle}")

        status = self.cf_service.get_user_status(handle)
        rating_history = self.cf_service.get_user_rating(handle)

        if not status or rating_history is None:
            return None

        # Filter strictly for in-contest submissions
        contest_subs = [
            sub for sub in status 
            if sub.get("author", {}).get("participantType") in ("CONTESTANT", "OUT_OF_COMPETITION")
        ]

        if not contest_subs:
            return ContestPerformanceProfile(
                handle=handle,
                total_contests_participated=len(rating_history),
                average_problems_solved=0.0,
                in_contest_weaknesses=[],
                speed_dropoff_point=None,
                accuracy_trend="Not enough contest data to determine accuracy.",
                rating_trend="No recent rating changes.",
                insights=["You have not participated in enough contests for detailed analytics."]
            )

        # 1. Group by Contest
        contests_dict: Dict[int, List[dict]] = defaultdict(list)
        for sub in contest_subs:
            cid = sub.get("contestId")
            if cid:
                contests_dict[cid].append(sub)

        total_contests = len(contests_dict)

        # 2. Analyze solves and accuracy
        total_subs = len(contest_subs)
        ok_subs = [s for s in contest_subs if s.get("verdict") == "OK"]
        total_ok = len(ok_subs)
        
        unique_solves = set()
        for s in ok_subs:
            prob = s.get("problem", {})
            unique_solves.add(f"{prob.get('contestId')}_{prob.get('index')}")
        
        avg_solved = len(unique_solves) / total_contests if total_contests > 0 else 0.0

        # Accuracy Trend
        accuracy_rate = total_ok / total_subs if total_subs > 0 else 0.0
        if accuracy_rate > 0.6:
            accuracy_trend = "High implementation accuracy under pressure."
        elif accuracy_rate > 0.3:
            accuracy_trend = "Moderate accuracy. You often require multiple penalties to get a problem accepted."
        else:
            accuracy_trend = "Low accuracy. You struggle significantly with implementation bugs during contests."

        # 3. In-contest weaknesses
        failed_tags_count = defaultdict(int)
        for sub in contest_subs:
            if sub.get("verdict") != "OK":
                for tag in sub.get("problem", {}).get("tags", []):
                    if not tag.startswith("*"):
                        failed_tags_count[tag] += 1
                        
        sorted_weaknesses = sorted(failed_tags_count.items(), key=lambda x: x[1], reverse=True)
        in_contest_weaknesses = [tag for tag, count in sorted_weaknesses[:3]]

        # 4. Speed Dropoff Point
        times_by_index = defaultdict(list)
        for s in ok_subs:
            index = s.get("problem", {}).get("index", "")
            base_index = ''.join([c for c in index if c.isalpha()]).upper()
            rel_time = s.get("relativeTimeSeconds")
            if base_index and rel_time is not None:
                times_by_index[base_index].append(rel_time)

        avg_time_by_index = {}
        for idx in "ABCDEFGHI":
            if times_by_index.get(idx) and len(times_by_index[idx]) >= 3:
                avg_time_by_index[idx] = sum(times_by_index[idx]) / len(times_by_index[idx])

        speed_dropoff = None
        prev_time = 0
        prev_idx = None
        largest_jump = 0
        dropoff_idx = None

        for idx in "ABCDEFGHI":
            if idx in avg_time_by_index:
                curr_time = avg_time_by_index[idx]
                if prev_idx:
                    jump = curr_time - prev_time
                    if jump > largest_jump and jump > 1800:
                        largest_jump = jump
                        dropoff_idx = idx
                prev_time = curr_time
                prev_idx = idx

        if dropoff_idx:
            speed_dropoff = f"Performance typically drops sharply at Problem {dropoff_idx}"

        # 5. Rating Trend
        if len(rating_history) >= 2:
            recent = rating_history[-5:]
            start_rating = recent[0].get("newRating", 0)
            end_rating = recent[-1].get("newRating", 0)
            if end_rating > start_rating + 50:
                rating_trend = "Consistently gaining rating."
            elif end_rating < start_rating - 50:
                rating_trend = "Currently on a downward rating trend."
            else:
                rating_trend = "Rating has been relatively stable recently."
        else:
            rating_trend = "Not enough recent contests to establish a trend."

        # 6. Generate Insights using LLM
        prompt = f"""
        Act as an elite competitive programming coach. Here are raw statistics for {handle} during live contests:
        - Accuracy: {accuracy_trend} (Rate: {accuracy_rate:.2f})
        - In-contest Weaknesses: {', '.join(in_contest_weaknesses) if in_contest_weaknesses else 'None'}
        - Speed Dropoff: {speed_dropoff if speed_dropoff else 'Steady solver'}
        - Average Problems Solved: {avg_solved:.1f}
        
        Write exactly 2 powerful, highly personalized, specific sentences of coaching advice based on this exact data.
        Focus strictly on fixing these specific in-contest habits. Do not mention standard generic advice. Do not output anything else.
        """
        try:
            llm_response = self.llm_service.generate_text(prompt)
            llm_insight = llm_response.strip()
            # Split sentences loosely if the LLM returned bullet points or newlines
            insights = [insight.strip('- *') for insight in llm_insight.split('\n') if len(insight.strip()) > 5]
            if not insights:
                insights = [llm_insight]
        except Exception as e:
            logger.error(f"LLM insight generation failed: {e}")
            insights = ["Focus on reducing penalty time and practicing problem types you frequently fail."]

        return ContestPerformanceProfile(
            handle=handle,
            total_contests_participated=len(rating_history),
            average_problems_solved=round(avg_solved, 2),
            in_contest_weaknesses=in_contest_weaknesses,
            speed_dropoff_point=speed_dropoff,
            accuracy_trend=accuracy_trend,
            rating_trend=rating_trend,
            insights=insights
        )

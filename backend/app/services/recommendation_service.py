import logging
import json
from typing import List, Optional

from app.services.problem_service import ProblemService
from app.services.codeforces_service import CodeforcesService
from app.services.profile_service import ProfileService
from app.services.llm.base import BaseLLMService
from app.schemas.recommendations import RecommendationItem, RecommendationResponse
from app.core.utils import ttl_cache

from app.services.probability_service import ProbabilityService

logger = logging.getLogger(__name__)

class RecommendationService:
    def __init__(
        self, 
        problem_service: ProblemService,
        codeforces_service: CodeforcesService,
        profile_service: ProfileService,
        probability_service: ProbabilityService = None,
        llm_service: BaseLLMService = None
    ):
        self.problem_service = problem_service
        self.codeforces_service = codeforces_service
        self.profile_service = profile_service
        self.probability_service = probability_service
        self.llm_service = llm_service

    def get_recommendations(
        self, 
        handle: str, 
        target_tag: Optional[str] = None, 
        target_rating: Optional[int] = None, 
        count: int = 5
    ) -> RecommendationResponse:
        
        # 1. Fetch user profile
        profile = self.profile_service.get_user_profile(handle)
        
        # Fetch user's solved status directly to filter out what they already did
        status = self.codeforces_service.get_user_status(handle) or []
        solved_ids = {f"{s.get('problem', {}).get('contestId')}{s.get('problem', {}).get('index')}" 
                      for s in status if s.get("verdict") == "OK"}

        recommendations: List[RecommendationItem] = []

        weak_tags = set()
        comfort_min = 800
        comfort_max = 1200

        if profile:
            weak_tags = set(profile.weak_tags)
            comfort_min = profile.comfort_zone_min
            comfort_max = profile.comfort_zone_max

        if target_tag:
            weak_tags.add(target_tag)

        if target_rating:
            comfort_min = target_rating - 100
            comfort_max = target_rating + 100

        # Target a broad rating band to capture 35%–85% solve probability
        search_min = comfort_min - 400
        search_max = comfort_max + 400

        # Use CF API cache as fallback so recommendations work even without scraped data
        all_problems = self.problem_service.get_all_problems(
            min_rating=search_min,
            max_rating=search_max,
            limit=200,
            shuffle=True,
        )

        pool = [p for p in all_problems if p.problem_id not in solved_ids and p.rating]
        pool = pool[:100]

        candidates_with_prob = []
        for p in pool:
            prob_score = 50.0
            if self.probability_service:
                prob_res = self.probability_service.calculate_probability(handle, p.problem_id, skip_llm=True, profile=profile)
                prob_score = prob_res.probability_percent
            
            # Hard filter: Don't show impossibly hard (<35%) or trivially easy (>85%)
            if prob_score < 35.0 or prob_score > 85.0:
                continue
                
            # Classify difficulty purely based on ML probability
            if prob_score >= 65.0:
                relation = "easy"
            elif prob_score >= 45.0:
                relation = "comfort"
            else:
                relation = "stretch"
                
            candidates_with_prob.append((p, "", relation, prob_score))

        # Sort descending by probability (Highest to Lowest)
        candidates_with_prob.sort(key=lambda x: x[3], reverse=True)

        # Select `count` evenly spaced problems to create a smooth descending difficulty curve!
        valid_candidates = []
        if len(candidates_with_prob) > count:
            step = len(candidates_with_prob) / count
            for i in range(count):
                idx = int(i * step)
                valid_candidates.append(candidates_with_prob[idx])
        else:
            valid_candidates = candidates_with_prob[:count]

        llm_reasons = []
        # Now pass the probability into the LLM Prompt for unified reasoning
        if valid_candidates and profile:
            prompt = f"Act as an elite competitive programming coach. User '{handle}' has a rating of {profile.current_rating or 1200}.\n"
            prompt += f"Weaknesses: {', '.join(profile.weak_tags)}\n"
            prompt += f"Strengths: {', '.join(profile.strong_tags)}\n"
            prompt += f"Unexplored Topics: {', '.join(profile.topics_unexplored)}\n\n"
            prompt += "I have selected the following problems for their curriculum. For each problem, I will provide the ML-calculated Probability of them solving it.\n\n"
            
            for p, reason, relation, prob_score in valid_candidates:
                prompt += f"Problem: {p.title} (Rating {p.rating})\nTags: {', '.join(p.tags)}\nPredicted Solve Probability: {prob_score}%\n\n"
                
            prompt += """Write a highly detailed, personalized coaching paragraph (3-4 sentences) for EACH problem explaining exactly WHY they must solve it.
Your reasoning MUST be deeply detailed and consider:
1. Their weak/unexplored tags vs the problem's tags.
2. Their current rating vs the problem's rating.
3. The specific predicted Solve Probability (e.g. 'Since you have a {prob_score}% chance, this is the perfect challenge to...').

You MUST output your response as a valid JSON array of strings (one string per problem in the exact order provided).
Do NOT include trailing commas. Ensure all strings are properly escaped.
Do NOT output any markdown formatting, backticks, or introduction text. Start strictly with '[' and end with ']'.

Example format:
[
  "Detailed reason 1...",
  "Detailed reason 2..."
]"""
            
            try:
                llm_response = self.llm_service.generate_text(prompt)
                start_idx = llm_response.find('[')
                end_idx = llm_response.rfind(']') + 1
                if start_idx != -1 and end_idx != -1:
                    cleaned_response = llm_response[start_idx:end_idx]
                    llm_reasons = json.loads(cleaned_response)
                else:
                    logger.error(f"LLM did not return a JSON array. Raw output: {llm_response}")
            except Exception as e:
                logger.error(f"Failed to generate LLM recommendation reasons. Error: {e}")
                logger.error(f"Raw LLM Response: {llm_response if 'llm_response' in locals() else 'None'}")

        # Build final response
        recommendation_list = []
        for i, (p, reason, relation, prob_score) in enumerate(valid_candidates):
            llm_reason = llm_reasons[i] if i < len(llm_reasons) else reason
            
            recommendation_list.append(
                RecommendationItem(
                    problem_id=p.problem_id,
                    title=p.title,
                    rating=p.rating or 0,
                    tags=p.tags,
                    url=p.url,
                    recommendation_reason=llm_reason.strip(),
                    difficulty_relation=relation,
                    solve_probability=prob_score
                )
            )

        return RecommendationResponse(
            handle=handle,
            recommendations=recommendation_list
        )

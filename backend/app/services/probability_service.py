import logging
import os
import joblib
import pandas as pd
from app.services.problem_service import ProblemService
from app.services.profile_service import ProfileService
from app.services.llm.base import BaseLLMService
from app.schemas.probability import SolveProbabilityResponse

logger = logging.getLogger(__name__)

# Load ML Model
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODEL_PATH = os.path.join(BASE_DIR, "ml_models", "solve_prob_model.joblib")
SCALER_PATH = os.path.join(BASE_DIR, "ml_models", "solve_prob_scaler.joblib")

class ProbabilityService:
    def __init__(self, profile_service: ProfileService, problem_service: ProblemService, llm_service: BaseLLMService = None):
        self.profile_service = profile_service
        self.problem_service = problem_service
        self.llm_service = llm_service
        self.model = None
        self.scaler = None
        if os.path.exists(MODEL_PATH) and os.path.exists(SCALER_PATH):
            try:
                self.model = joblib.load(MODEL_PATH)
                self.scaler = joblib.load(SCALER_PATH)
                logger.info("Loaded ML Probability Model and Scaler successfully.")
            except Exception as e:
                logger.error(f"Failed to load ML Probability Model: {e}")

    def calculate_probability(self, handle: str, problem_id: str, skip_llm: bool = False, profile=None) -> SolveProbabilityResponse:
        if not profile:
            profile = self.profile_service.get_user_profile(handle)
        problem = self.problem_service.get_problem(problem_id)
        
        if not profile or not problem:
            return SolveProbabilityResponse(
                handle=handle,
                problem_id=problem_id,
                probability_percent=0.0,
                factors=["Unable to load profile or problem data."]
            )

        # Base properties
        problem_rating = problem.rating or 800
        
        # Cold start detection: If they have a rating, they are definitely not a cold start!
        is_cold_start = 1 if profile.current_rating is None else 0
        
        # We don't have total_solved in Profile schema yet, so assume reasonable defaults if not cold start
        total_solved = getattr(profile, 'total_solved_count', 150 if not is_cold_start else 0)
        contest_maturity = getattr(profile, 'contest_participations', 10 if not is_cold_start else 0)

        if is_cold_start:
            user_rating = 800
            user_max_rating = 800
            avg_max_index = 1.0
        else:
            user_rating = profile.current_rating or profile.comfort_zone_min or 1200
            user_max_rating = profile.max_rating or user_rating
            avg_max_index = max(1.0, min(6.0, (user_rating - 800) / 300)) # Approximation if not in profile

        # Extract features
        rating_difference = problem_rating - user_rating
        user_max_rating_diff = user_max_rating - user_rating
        
        # Problem index encoded (A=1, B=2, etc.)
        idx_char = ''.join([c for c in problem_id if c.isalpha()])
        if idx_char:
            problem_index = ord(idx_char[0].upper()) - 64
        else:
            problem_index = 1
        problem_index = max(1, min(6, problem_index))
        
        index_gap = problem_index - avg_max_index

        features = {
            "rating_difference": [rating_difference],
            "user_max_rating_diff": [user_max_rating_diff],
            "problem_index_encoded": [problem_index],
            "total_solved_count": [total_solved],
            "contest_maturity": [contest_maturity],
            "index_gap": [index_gap],
            "is_cold_start": [is_cold_start]
        }
        
        df = pd.DataFrame(features)
        factors = [
            f"Rating Diff: {rating_difference}",
            f"Index Gap: {index_gap:.1f}",
            f"Total Solves: {total_solved}",
            f"Cold Start: {'Yes' if is_cold_start else 'No'}"
        ]

        if self.model and self.scaler:
            try:
                scaled_df = self.scaler.transform(df)
                prob = self.model.predict_proba(scaled_df)[0][1] * 100.0
                factors.append("Calculated via Deep Neural Network (MLP).")
            except Exception as e:
                logger.error(f"ML Model prediction failed: {e}")
                prob = 50.0
                factors.append("Model inference failed, defaulting to 50%")
        else:
            # Fallback Elo math if model isn't trained yet
            elo_prob = 1.0 / (1.0 + 10.0 ** (rating_difference / 400.0))
            prob = elo_prob * 100.0
            if is_cold_start and problem_rating > 1000:
                prob *= 0.2
            factors.append("Calculated via Fallback Elo Math (ML Model not found).")

        final_probability = max(0.01, min(99.9, prob))
        
        llm_reasoning = None
        if self.llm_service and not skip_llm:
            prompt = f"""
Act as an elite competitive programming coach.
User '{handle}' has a rating of {user_rating} and {total_solved} total solves.
They are considering solving Problem '{problem.title}' (Rating {problem_rating}, Index {idx_char}).
My Machine Learning model predicts they have a {final_probability:.1f}% chance of solving it.
Write exactly ONE concise, human-readable sentence explaining WHY this is their probability based on their rating difference ({rating_difference}) and their index gap vs average. 
Make it sound like an insight. Do not mention "machine learning model" or "neural network".
"""
            try:
                llm_response = self.llm_service.generate_text(prompt)
                llm_reasoning = llm_response.strip().replace('\n', ' ')
            except Exception as e:
                logger.error(f"Failed to generate LLM reasoning for probability: {e}")

        return SolveProbabilityResponse(
            handle=handle,
            problem_id=problem_id,
            probability_percent=round(final_probability, 1),
            factors=factors,
            llm_reasoning=llm_reasoning
        )

import logging
import os
import joblib
import pandas as pd

from app.services.problem_service import ProblemService
from app.services.profile_service import ProfileService
from app.services.llm.base import BaseLLMService
from app.schemas.probability import SolveProbabilityResponse

logger = logging.getLogger(__name__)

BASE_DIR      = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ENSEMBLE_PATH = os.path.join(BASE_DIR, "ml_models", "solve_prob_ensemble.joblib")
LEGACY_PATH   = os.path.join(BASE_DIR, "ml_models", "solve_prob_model.joblib")
SCALER_PATH   = os.path.join(BASE_DIR, "ml_models", "solve_prob_scaler.joblib")

# Feature order must match train_probability_model.py FEATURES list exactly
FEATURE_COLS = [
    "rating_difference",
    "user_max_rating_diff",
    "problem_index_encoded",
    "total_solved_count",
    "contest_maturity",
    "index_gap",
    "is_cold_start",
    "rating_ratio",
    "elo_baseline",
    "experience_tier",
    "difficulty_tier",
    "rating_volatility",
    "comfort_zone_distance",
    "solve_rate_proxy",
    "is_stretch_problem",
]


class ProbabilityService:
    def __init__(
        self,
        profile_service: ProfileService,
        problem_service: ProblemService,
        llm_service: BaseLLMService = None,
    ):
        self.profile_service = profile_service
        self.problem_service = problem_service
        self.llm_service     = llm_service
        self.model           = None
        self.scaler          = None   # only used by legacy MLP model
        self._is_ensemble    = False

        # Try new stacking ensemble first, fall back to legacy MLP
        if os.path.exists(ENSEMBLE_PATH):
            try:
                self.model        = joblib.load(ENSEMBLE_PATH)
                self._is_ensemble = True
                logger.info("Loaded XGBoost Stacking Ensemble successfully.")
            except Exception as e:
                logger.error(f"Failed to load stacking ensemble: {e}")
        elif os.path.exists(LEGACY_PATH) and os.path.exists(SCALER_PATH):
            try:
                self.model  = joblib.load(LEGACY_PATH)
                self.scaler = joblib.load(SCALER_PATH)
                logger.info("Loaded legacy MLP probability model.")
            except Exception as e:
                logger.error(f"Failed to load legacy ML model: {e}")

    # ── Public interface ──────────────────────────────────────────────────────

    def calculate_probability(
        self,
        handle: str,
        problem_id: str,
        skip_llm: bool = False,
        profile=None,
    ) -> SolveProbabilityResponse:
        if not profile:
            profile = self.profile_service.get_user_profile(handle)
        problem = self.problem_service.get_problem(problem_id)

        if not profile or not problem:
            return SolveProbabilityResponse(
                handle=handle,
                problem_id=problem_id,
                probability_percent=0.0,
                factors=["Unable to load profile or problem data."],
            )

        # ── Raw user + problem values ─────────────────────────────────────
        problem_rating   = problem.rating or 800
        is_cold_start    = 1 if profile.current_rating is None else 0
        total_solved     = getattr(profile, "total_solved_count", 150 if not is_cold_start else 0)
        contest_maturity = getattr(profile, "contest_participations", 10 if not is_cold_start else 0)

        if is_cold_start:
            user_rating    = 800
            user_max_rating = 800
            avg_max_index  = 1.0
        else:
            user_rating    = profile.current_rating or profile.comfort_zone_min or 1200
            user_max_rating = profile.max_rating or user_rating
            avg_max_index  = max(1.0, min(6.0, (user_rating - 800) / 300))

        # Problem letter index: A=1, B=2, …
        idx_char = "".join(c for c in problem_id if c.isalpha())
        if idx_char:
            problem_index = ord(idx_char[0].upper()) - 64
        else:
            problem_index = 1
        problem_index = max(1, min(6, problem_index))

        # ── Original 7 features ───────────────────────────────────────────
        rating_difference    = problem_rating - user_rating
        user_max_rating_diff = user_max_rating - user_rating
        index_gap            = problem_index - avg_max_index

        # ── New 8 features ────────────────────────────────────────────────
        rating_ratio          = problem_rating / max(user_rating, 1)
        elo_baseline          = 1.0 / (1.0 + 10.0 ** (rating_difference / 400.0))
        experience_tier       = min(4, total_solved // 250)
        difficulty_tier       = min(4, max(0, (problem_rating - 800) // 400))
        rating_volatility     = user_max_rating - user_rating
        comfort_zone_center   = user_rating + 200
        comfort_zone_distance = abs(problem_rating - comfort_zone_center)
        solve_rate_proxy      = total_solved / (contest_maturity + 1)
        is_stretch_problem    = 1 if problem_rating > user_rating + 200 else 0

        df = pd.DataFrame([{
            "rating_difference":     rating_difference,
            "user_max_rating_diff":  user_max_rating_diff,
            "problem_index_encoded": problem_index,
            "total_solved_count":    total_solved,
            "contest_maturity":      contest_maturity,
            "index_gap":             index_gap,
            "is_cold_start":         is_cold_start,
            "rating_ratio":          rating_ratio,
            "elo_baseline":          elo_baseline,
            "experience_tier":       experience_tier,
            "difficulty_tier":       difficulty_tier,
            "rating_volatility":     rating_volatility,
            "comfort_zone_distance": comfort_zone_distance,
            "solve_rate_proxy":      solve_rate_proxy,
            "is_stretch_problem":    is_stretch_problem,
        }])[FEATURE_COLS]

        factors = [
            f"Rating Diff: {rating_difference:+d}",
            f"Elo Baseline: {elo_baseline:.0%}",
            f"Index Gap: {index_gap:+.1f}",
            f"Experience Tier: {experience_tier}/4",
            f"Stretch Problem: {'Yes' if is_stretch_problem else 'No'}",
        ]

        # ── Inference ─────────────────────────────────────────────────────
        if self.model:
            try:
                if self._is_ensemble:
                    # Ensemble (StackingClassifier) includes its own scaler pipeline for MLP
                    prob = self.model.predict_proba(df)[0][1] * 100.0
                    factors.append("Model: XGBoost Stacking Ensemble (XGB + LGB + MLP).")
                else:
                    # Legacy: external scaler required for MLP-only model
                    scaled = self.scaler.transform(df[FEATURE_COLS[:7]])
                    prob = self.model.predict_proba(scaled)[0][1] * 100.0
                    factors.append("Model: Deep Neural Network (MLP) — legacy.")
            except Exception as e:
                logger.error(f"ML model prediction failed: {e}")
                prob = 50.0
                factors.append("Model inference failed — defaulting to 50%.")
        else:
            # Pure Elo fallback when no model is trained yet
            prob = elo_baseline * 100.0
            if is_cold_start and problem_rating > 1000:
                prob *= 0.2
            factors.append("Fallback: Elo math (ensemble not yet trained).")

        final_probability = max(0.1, min(99.9, prob))

        # ── Optional LLM narrative ────────────────────────────────────────
        llm_reasoning = None
        if self.llm_service and not skip_llm:
            prompt = (
                f"Act as an elite competitive programming coach. "
                f"User '{handle}' has rating {user_rating} and {total_solved} total solves. "
                f"They're considering '{problem.title}' (rating {problem_rating}, index {idx_char or '?'}). "
                f"Our XGBoost Stacking Ensemble predicts a {final_probability:.1f}% solve probability. "
                f"Write exactly one concise sentence explaining why — reference their rating gap ({rating_difference:+d}), "
                f"their experience tier ({experience_tier}/4), and whether this is a stretch problem. "
                f"Do not mention 'machine learning' or 'model'. Sound like a coach insight."
            )
            try:
                llm_reasoning = self.llm_service.generate_text(prompt).strip().replace("\n", " ")
            except Exception as e:
                logger.error(f"LLM probability reasoning failed: {e}")

        return SolveProbabilityResponse(
            handle=handle,
            problem_id=problem_id,
            probability_percent=round(final_probability, 1),
            factors=factors,
            llm_reasoning=llm_reasoning,
        )

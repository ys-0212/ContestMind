import logging
from typing import Optional
from collections import Counter
from datetime import datetime

from app.schemas.profile import UserProfile
from app.services.codeforces_service import CodeforcesService
from app.services.analytics_service import AnalyticsService
from app.services.attempt_service import AttemptService

logger = logging.getLogger(__name__)

class ProfileService:
    def __init__(
        self,
        codeforces_service: CodeforcesService,
        analytics_service: AnalyticsService,
        attempt_service: AttemptService
    ):
        self.cf_service = codeforces_service
        self.analytics_service = analytics_service
        self.attempt_service = attempt_service

    def get_user_profile(self, handle: str) -> Optional[UserProfile]:
        logger.info(f"Generating profile for {handle}")
        
        # 1. Fetch user info to get rating
        user_info = self.cf_service.get_user_info(handle)
        if not user_info:
            return None
            
        current_rating = user_info.get("rating", None)
        
        # 2. Calculate Comfort Zone
        if current_rating:
            comfort_min = max(800, current_rating - 100)
            comfort_max = current_rating + 200
        else:
            # Default for unrated users
            comfort_min = 800
            comfort_max = 1000
            
        # 3. Fetch weaknesses/strengths from Analytics
        analytics = self.analytics_service.analyze_weaknesses(handle)
        weak_tags = []
        strong_tags = []
        if analytics:
            # Safely extract tags, checking for proper schema
            weak_tags = analytics.weakest_tags[:5] if hasattr(analytics, "weakest_tags") else []
            strong_tags = analytics.strongest_tags[:5] if hasattr(analytics, "strongest_tags") else []
            
        # 4. Fetch recent attempts
        attempts = self.attempt_service.get_user_attempts(handle)
        attempts_summary = dict(Counter([a.outcome for a in attempts]))
        
        return UserProfile(
            handle=handle,
            current_rating=user_info.get("rating"),
            max_rating=user_info.get("maxRating"),
            rank=user_info.get("rank"),
            avatar_url=user_info.get("avatar"),
            comfort_zone_min=comfort_min,
            comfort_zone_max=comfort_max,
            weak_tags=weak_tags,
            strong_tags=strong_tags,
            topics_explored=analytics.topics_explored if hasattr(analytics, "topics_explored") else [],
            topics_unexplored=analytics.topics_unexplored if hasattr(analytics, "topics_unexplored") else [],
            holistic_weakness_insights=analytics.holistic_weakness_insights if hasattr(analytics, "holistic_weakness_insights") else [],
            recent_attempts_summary=attempts_summary,
            last_updated=datetime.utcnow()
        )

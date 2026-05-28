import logging
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query

from app.schemas.recommendations import RecommendationResponse
from app.services.recommendation_service import RecommendationService
from app.api.deps import get_recommendation_service

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/", response_model=RecommendationResponse)
def get_recommendations(
    handle: str,
    target_tag: Optional[str] = Query(None, description="Optional tag to focus recommendations on"),
    target_rating: Optional[int] = Query(None, description="Optional rating to focus recommendations on"),
    count: int = Query(5, ge=1, le=20, description="Number of recommendations to return"),
    recommendation_service: RecommendationService = Depends(get_recommendation_service)
):
    """
    Generates personalized problem recommendations based on a user's Codeforces history and weaknesses.
    """
    logger.info(f"Received recommendation request for handle: {handle}")
    
    try:
        response = recommendation_service.get_recommendations(
            handle=handle,
            target_tag=target_tag,
            target_rating=target_rating,
            count=count
        )
        return response
    except ValueError as e:
        logger.warning(f"Error generating recommendations for handle {handle}: {e}")
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error in recommendations for handle {handle}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal error calculating recommendations.")

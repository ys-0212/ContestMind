import logging
from fastapi import APIRouter, Depends, HTTPException

from app.schemas.analytics import AnalyticsResponse
from app.services.analytics_service import AnalyticsService
from app.api.deps import get_analytics_service

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/weaknesses", response_model=AnalyticsResponse)
def get_user_weaknesses(
    handle: str,
    analytics_service: AnalyticsService = Depends(get_analytics_service)
):
    """
    Analyzes a user's Codeforces history to generate a personalized weaknesses dashboard.
    """
    logger.info(f"Received analytics request for handle: {handle}")
    
    try:
        response = analytics_service.analyze_weaknesses(handle)
        return response
    except ValueError as e:
        logger.warning(f"Error fetching analytics for handle {handle}: {e}")
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error in analytics for handle {handle}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal error calculating analytics.")

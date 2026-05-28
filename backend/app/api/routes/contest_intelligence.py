import logging
from fastapi import APIRouter, Depends, HTTPException

from app.schemas.contest_intelligence import ContestPerformanceProfile
from app.services.contest_intelligence_service import ContestIntelligenceService
from app.api.deps import get_contest_intelligence_service

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/{handle}", response_model=ContestPerformanceProfile)
def get_contest_intelligence(
    handle: str,
    contest_service: ContestIntelligenceService = Depends(get_contest_intelligence_service)
):
    """
    Get heuristic-based intelligence about a user's performance 
    specifically during live contests.
    """
    profile = contest_service.analyze_contest_performance(handle)
    if not profile:
        raise HTTPException(status_code=404, detail="User not found or no contest data available.")
    return profile

import logging
from fastapi import APIRouter, Depends, HTTPException

from app.schemas.profile import UserProfile
from app.services.profile_service import ProfileService
from app.api.deps import get_profile_service

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/{handle}", response_model=UserProfile)
def get_user_profile(
    handle: str,
    profile_service: ProfileService = Depends(get_profile_service)
):
    """
    Get the aggregated user intelligence profile, including comfort zone, 
    weaknesses, strengths, and recent attempts summary.
    """
    profile = profile_service.get_user_profile(handle)
    if not profile:
        raise HTTPException(status_code=404, detail="User not found or unable to generate profile.")
    return profile

@router.get("/{handle}/rating")
def get_user_rating(
    handle: str,
    profile_service: ProfileService = Depends(get_profile_service)
):
    """
    Get the user's Codeforces rating history.
    """
    rating_data = profile_service.cf_service.get_user_rating(handle)
    if rating_data is None:
        raise HTTPException(status_code=404, detail="Rating history not found.")
    return {"rating_changes": rating_data}

@router.get("/{handle}/submissions")
def get_recent_submissions(
    handle: str,
    limit: int = 10,
    profile_service: ProfileService = Depends(get_profile_service)
):
    """
    Get the user's recent submissions from Codeforces.
    """
    status = profile_service.cf_service.get_user_status(handle)
    if status is None:
        raise HTTPException(status_code=404, detail="Submissions not found.")
    
    # Extract recent submissions
    recent = []
    for s in status[:limit]:
        p = s.get("problem", {})
        recent.append({
            "problem_id": f"{p.get('contestId', '')}{p.get('index', '')}",
            "title": p.get("name", ""),
            "creation_time": s.get("creationTimeSeconds", 0),
            "verdict": s.get("verdict", "UNKNOWN")
        })
    return {"recent_attempts": recent}

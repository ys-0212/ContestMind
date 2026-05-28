import logging
from typing import List
from fastapi import APIRouter, Depends, HTTPException

from app.schemas.attempt import AttemptCreate, AttemptResponse
from app.services.attempt_service import AttemptService
from app.api.deps import get_attempt_service

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("", response_model=AttemptResponse)
def record_attempt(
    attempt: AttemptCreate,
    attempt_service: AttemptService = Depends(get_attempt_service)
):
    """
    Record a user's attempt at a problem.
    """
    result = attempt_service.record_attempt(attempt)
    if not result:
        raise HTTPException(status_code=500, detail="Failed to record attempt. Ensure Supabase is configured.")
    return result

@router.get("/{handle}", response_model=List[AttemptResponse])
def get_user_attempts(
    handle: str,
    attempt_service: AttemptService = Depends(get_attempt_service)
):
    """
    Get all attempts for a specific user, ordered by most recent first.
    """
    return attempt_service.get_user_attempts(handle)

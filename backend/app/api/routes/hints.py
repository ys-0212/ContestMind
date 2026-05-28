from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from app.schemas.hint import HintRequestCreate, HintRequestResponse
from app.services.hint_service import HintService
from app.api.deps import get_hint_service

router = APIRouter()

class MaxHintResponse(BaseModel):
    handle: str
    problem_id: str
    max_hint_level: int

@router.post("/", response_model=HintRequestResponse, status_code=status.HTTP_201_CREATED)
def record_hint_request(
    request: HintRequestCreate,
    hint_service: HintService = Depends(get_hint_service)
):
    """Record that a user has requested a specific hint level for a problem."""
    result = hint_service.record_hint(request)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to record hint request."
        )
    return result

@router.get("/{handle}/{problem_id}", response_model=MaxHintResponse)
def get_max_hint(
    handle: str,
    problem_id: str,
    hint_service: HintService = Depends(get_hint_service)
):
    """Retrieve the maximum hint level the user has requested for this problem."""
    max_level = hint_service.get_max_hint_level(handle, problem_id)
    return MaxHintResponse(
        handle=handle,
        problem_id=problem_id,
        max_hint_level=max_level
    )

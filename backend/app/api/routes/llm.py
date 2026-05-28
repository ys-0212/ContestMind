import logging
from fastapi import APIRouter, Depends, HTTPException

from app.schemas.llm import HintRequest, HintResponse
from app.services.hint_service import HintService
from app.api.deps import get_hint_service

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/hints", response_model=HintResponse)
def get_progressive_hints(
    request: HintRequest,
    hint_service: HintService = Depends(get_hint_service)
):
    """
    Generates adaptive progressive hints (Levels 1-3) for a problem.
    """
    logger.info(f"Received hint request for problem_id: {request.problem_id}, level: {request.current_hint_level}")
    
    try:
        hint_response = hint_service.generate_hint(request)
        return hint_response
    except ValueError as e:
        logger.warning(f"Validation error generating hint: {e}")
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"An unexpected error occurred during hint generation for problem {request.problem_id}", exc_info=True)
        raise HTTPException(status_code=500, detail="An internal error occurred during hint generation.")

from fastapi import APIRouter, Depends, HTTPException
from app.schemas.probability import SolveProbabilityResponse
from app.services.probability_service import ProbabilityService
from app.api.deps import get_probability_service

router = APIRouter()

@router.get("/{handle}/{problem_id}", response_model=SolveProbabilityResponse)
def get_solve_probability(
    handle: str,
    problem_id: str,
    probability_service: ProbabilityService = Depends(get_probability_service)
):
    """
    Calculates the likelihood (0-100%) of a user solving a specific problem.
    """
    try:
        response = probability_service.calculate_probability(handle, problem_id)
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error calculating probability: {str(e)}")

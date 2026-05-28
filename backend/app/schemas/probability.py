from typing import List, Optional
from pydantic import BaseModel, Field

class SolveProbabilityResponse(BaseModel):
    handle: str
    problem_id: str
    probability_percent: float = Field(..., description="Calculated likelihood of solving (0-100)")
    factors: List[str] = Field(..., description="Explanations for the calculated probability")
    llm_reasoning: Optional[str] = Field(None, description="Human-readable LLM explanation of the probability score")

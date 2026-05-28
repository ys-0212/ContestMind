from pydantic import BaseModel, Field
from typing import List, Optional

class RecommendationItem(BaseModel):
    problem_id: str
    title: str
    rating: Optional[int] = None
    tags: List[str]
    url: str
    recommendation_reason: str
    difficulty_relation: str # "easy", "comfort", "stretch"
    solve_probability: Optional[float] = Field(None, description="Heuristic probability of solving (0-100%)")

class RecommendationResponse(BaseModel):
    handle: str
    recommendations: List[RecommendationItem]

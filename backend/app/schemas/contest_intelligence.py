from typing import List, Optional
from pydantic import BaseModel, Field

class ContestPerformanceProfile(BaseModel):
    handle: str = Field(..., description="Codeforces handle")
    total_contests_participated: int = Field(..., description="Number of rated contests")
    average_problems_solved: float = Field(..., description="Average number of problems solved per contest")
    in_contest_weaknesses: List[str] = Field(default_factory=list, description="Tags frequently failed during contests")
    speed_dropoff_point: Optional[str] = Field(None, description="The problem index where speed drops sharply")
    accuracy_trend: str = Field(..., description="Description of the user's in-contest accuracy")
    rating_trend: str = Field(..., description="Recent rating trajectory (e.g. gaining/losing)")
    insights: List[str] = Field(default_factory=list, description="Coaching insights generated from heuristics")

from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field

class AttemptCreate(BaseModel):
    handle: str = Field(..., description="Codeforces handle of the user")
    problem_id: str = Field(..., description="The problem ID, e.g., '1900C'")
    outcome: str = Field(..., description="E.g., 'solved', 'attempted', 'failed', 'partial'")
    difficulty_perception: Optional[str] = Field(None, description="E.g., 'easy', 'medium', 'hard'")
    time_spent_seconds: Optional[int] = Field(None, description="Time spent in seconds")
    hints_used: int = Field(0, description="Number of hints used")

class AttemptResponse(AttemptCreate):
    id: str
    created_at: datetime

    class Config:
        from_attributes = True

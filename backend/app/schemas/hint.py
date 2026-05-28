from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field

class HintRequestCreate(BaseModel):
    handle: str = Field(..., description="Codeforces handle of the user")
    problem_id: str = Field(..., description="ID of the problem (e.g., 1234A)")
    hint_level: int = Field(..., description="The hint level requested (1=Observation, 2=Algorithm, etc.)")

class HintRequestResponse(BaseModel):
    id: str = Field(..., description="UUID of the hint request record")
    handle: str
    problem_id: str
    hint_level: int
    created_at: datetime

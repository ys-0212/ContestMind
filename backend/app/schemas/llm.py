from typing import List
from pydantic import BaseModel, Field

class HintRequest(BaseModel):
    problem_id: str
    current_hint_level: int = Field(1, ge=1, le=3, description="1: Constraints, 2: Algorithm, 3: Implementation")
    previous_hints: List[str] = Field(default_factory=list, description="Text of hints already revealed, for continuity")

class HintResponse(BaseModel):
    problem_id: str
    hint_level: int
    hint_text: str

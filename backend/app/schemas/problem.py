from pydantic import BaseModel, Field
from typing import List, Optional


class ProblemExample(BaseModel):
    input: str = ""
    output: str = ""
    explanation: Optional[str] = None


class Problem(BaseModel):
    problem_id: str = Field(..., description="Unique identifier, e.g. '1700A'")
    title: str
    rating: Optional[int] = None
    tags: List[str] = []
    url: str
    statement: Optional[str] = None
    editorial: Optional[str] = None
    source: str = Field(..., description="e.g. 'codeforces'")
    # Structured examples extracted from the statement
    examples: List[ProblemExample] = []
    # True when a full scraped statement is available locally
    has_statement: bool = False

    class Config:
        from_attributes = True

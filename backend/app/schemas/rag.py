from pydantic import BaseModel, Field
from typing import List

from .retrieval import SearchResult

class SimplifyRequest(BaseModel):
    query: str = Field(..., min_length=3, description="The user query or problem topic to simplify.")

class SimplifyResponse(BaseModel):
    query: str
    simplified_editorial: str
    retrieved_context: List[SearchResult]
    sources_used: List[str] = Field(..., description="List of problem IDs from the retrieved context.")

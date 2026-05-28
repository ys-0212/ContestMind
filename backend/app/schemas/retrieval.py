from pydantic import BaseModel, Field
from typing import List, Optional

class SearchRequest(BaseModel):
    query: str = Field(..., min_length=3, description="The search query text.")
    top_k: int = Field(5, gt=0, le=20, description="The number of results to return.")

class SearchResult(BaseModel):
    problem_id: str
    title: str
    rating: Optional[int] = None
    tags: List[str]
    url: str
    similarity_score: float = Field(..., description="A score from 0.0 to 1.0 indicating relevance.")
    preview: str = Field(..., description="A short preview of the document content.")

class SearchResponse(BaseModel):
    query: str
    results: List[SearchResult]
    count: int

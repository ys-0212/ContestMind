from typing import List, Dict, Optional, Any
from datetime import datetime
from pydantic import BaseModel, Field

class UserProfile(BaseModel):
    handle: str = Field(..., description="Codeforces handle")
    current_rating: Optional[int] = Field(None, description="Current Codeforces rating")
    max_rating: Optional[int] = Field(None, description="Max Codeforces rating")
    rank: Optional[str] = Field(None, description="Codeforces rank")
    avatar_url: Optional[str] = Field(None, description="Avatar URL")
    comfort_zone_min: int = Field(..., description="Lower bound of comfort zone")
    comfort_zone_max: int = Field(..., description="Upper bound of comfort zone")
    weak_tags: List[str] = Field(default_factory=list, description="Top weakness tags")
    strong_tags: List[str] = Field(default_factory=list, description="Top 5 tags the user solves successfully")
    topics_explored: List[str] = Field(default_factory=list, description="Broad domains the user has explored")
    topics_unexplored: List[str] = Field(default_factory=list, description="Broad domains the user has NOT explored")
    holistic_weakness_insights: List[str] = Field(default_factory=list, description="Deep holistic LLM gap analysis")
    recent_attempts_summary: Dict[str, Any] = Field(default_factory=dict, description="Summary of recent local platform attempts")
    last_updated: datetime = Field(default_factory=datetime.utcnow)

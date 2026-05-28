from pydantic import BaseModel, Field
from typing import List, Dict, Optional

class TagAnalytics(BaseModel):
    tag: str
    solved_count: int
    average_rating: Optional[float] = None

class DifficultyDistribution(BaseModel):
    rating_range: str
    solved_count: int

class AnalyticsResponse(BaseModel):
    handle: str
    current_rating: Optional[int] = None
    max_rating: Optional[int] = None
    weakest_tags: List[str]
    strongest_tags: List[str]
    average_solved_rating: Optional[int]
    highest_solved_rating: Optional[int]
    recent_activity_trend: str
    rating_comfort_zone: str
    tag_solve_distribution: Dict[str, int]
    topics_explored: List[str] = Field(default_factory=list, description="Broad domains the user has explored")
    topics_unexplored: List[str] = Field(default_factory=list, description="Broad domains the user has NOT explored")
    difficulty_distribution: List[DifficultyDistribution] = Field(..., description="Distribution of solved problems by difficulty")
    contest_participation_summary: str = Field(..., description="Summary of user's contest history")
    holistic_weakness_insights: List[str] = Field(default_factory=list, description="Deep LLM-driven holistic gap analysis covering all topics and missing blind spots")
    unsolved_high_rating_attempts: List[str] = Field(default_factory=list, description="Top 5 unsolved problems above user's average rating")

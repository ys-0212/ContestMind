from pydantic import BaseModel, Field
from typing import List, Optional

class ChatMessage(BaseModel):
    role: str = Field(..., description="Role of the sender (user, assistant)")
    content: str = Field(..., description="Content of the message")

class ChatRequest(BaseModel):
    query: str = Field(..., description="The user's question or prompt")
    history: Optional[List[ChatMessage]] = Field(default=[], description="Previous conversation history (deprecated, use session_id instead)")
    handle: Optional[str] = Field(None, description="Optional user handle for personalized answers")
    session_id: Optional[str] = Field(None, description="The ID of the chat session to append to")
    user_id: Optional[str] = Field(None, description="The authenticated user's ID")
    # Problem workspace context — populated by the frontend problem page
    problem_id: Optional[str] = Field(None, description="Current problem ID")
    problem_title: Optional[str] = Field(None, description="Current problem title")
    problem_tags: Optional[List[str]] = Field(None, description="Problem topic tags")
    problem_rating: Optional[int] = Field(None, description="Problem difficulty rating")
    user_code: Optional[str] = Field(None, description="User's current code (may be truncated)")
    run_status: Optional[str] = Field(None, description="Last execution verdict: accepted|wrong_answer|compile_error|runtime_error|tle|error")
    run_stdout: Optional[str] = Field(None, description="Last execution stdout (may be truncated)")
    run_stderr: Optional[str] = Field(None, description="Last execution stderr/compiler output (may be truncated)")
    stdin_used: Optional[str] = Field(None, description="Stdin used in the last run")
    expected_output: Optional[str] = Field(None, description="Expected output used in the last run")

class ChatResponse(BaseModel):
    response_text: str = Field(..., description="The AI's generated response")

from fastapi import APIRouter, Depends, HTTPException

from app.schemas.chat import ChatRequest, ChatResponse
from app.api.deps import get_chat_service
from app.services.chat_service import ChatService

router = APIRouter(tags=["chat"])

@router.post("/ask", response_model=ChatResponse)
def ask_chat_assistant(
    request: ChatRequest,
    chat_service: ChatService = Depends(get_chat_service)
):
    """
    General conversational endpoint for Competitive Programming doubts.
    Retrieves relevant CP context from ChromaDB based on the user's query.
    """
    try:
        response = chat_service.generate_chat_response(request)
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any
from app.api.deps import supabase_client

router = APIRouter(prefix="/history", tags=["history"])

@router.get("/sessions/{user_id}")
def get_user_sessions(user_id: str):
    """
    Retrieve all chat sessions for a given user.
    """
    if not supabase_client:
        raise HTTPException(status_code=503, detail="Database connection unavailable")
    
    try:
        res = supabase_client.table("chat_sessions")\
            .select("id, title, created_at, updated_at")\
            .eq("user_id", user_id)\
            .order("updated_at", desc=True)\
            .execute()
        return {"sessions": res.data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/chats/{session_id}")
def get_chat_history(session_id: str):
    """
    Retrieve all messages in a specific chat session.
    """
    if not supabase_client:
        raise HTTPException(status_code=503, detail="Database connection unavailable")
    
    try:
        res = supabase_client.table("chat_messages")\
            .select("role, content, created_at")\
            .eq("session_id", session_id)\
            .order("created_at", desc=False)\
            .execute()
        return {"messages": res.data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

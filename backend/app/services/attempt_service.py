import logging
from typing import List, Optional
from supabase import create_client, Client

from app.core.config import settings
from app.schemas.attempt import AttemptCreate, AttemptResponse

logger = logging.getLogger(__name__)

class AttemptService:
    def __init__(self):
        if not settings.SUPABASE_URL or not settings.SUPABASE_KEY:
            logger.warning("Supabase URL or Key not set. Attempts tracking will be disabled/mocked.")
            self.client: Optional[Client] = None
        else:
            self.client = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
            
    def record_attempt(self, attempt: AttemptCreate) -> Optional[AttemptResponse]:
        if not self.client:
            logger.error("Cannot record attempt: Supabase client not initialized.")
            return None
            
        try:
            data = attempt.model_dump()
            response = self.client.table("user_attempts").insert(data).execute()
            if response.data and len(response.data) > 0:
                return AttemptResponse(**response.data[0])
            return None
        except Exception as e:
            logger.error(f"Failed to record attempt in Supabase: {e}")
            return None

    def get_user_attempts(self, handle: str) -> List[AttemptResponse]:
        if not self.client:
            logger.error("Cannot fetch attempts: Supabase client not initialized.")
            return []
            
        try:
            response = self.client.table("user_attempts").select("*").eq("handle", handle).order("created_at", desc=True).execute()
            if response.data:
                return [AttemptResponse(**row) for row in response.data]
            return []
        except Exception as e:
            logger.error(f"Failed to fetch user attempts from Supabase for {handle}: {e}")
            return []

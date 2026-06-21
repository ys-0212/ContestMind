import logging
from typing import Optional
from supabase import create_client, Client

from app.core.config import settings

logger = logging.getLogger(__name__)

class SupabaseService:
    def __init__(self):
        self._client: Optional[Client] = None
        
        if not settings.SUPABASE_URL or not settings.SUPABASE_KEY:
            logger.warning("Supabase URL or Key not set. Supabase client will not be initialized.")
        else:
            try:
                self._client = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
                logger.info("Supabase client initialized successfully.")
            except Exception as e:
                logger.error(f"Failed to initialize Supabase client: {e}")
                
    @property
    def client(self) -> Client:
        if not self._client:
            raise RuntimeError("Supabase client is not initialized.")
        return self._client

# d:\Project\ContestMind\backend\app\services\vector_service.py
import logging
from typing import List, Dict, Any
from sentence_transformers import SentenceTransformer
from supabase import Client

from app.core.config import settings

logger = logging.getLogger(__name__)


class VectorService:
    def __init__(self, supabase_client: Client):
        """
        Initializes the VectorService using Supabase pgvector.
        """
        try:
            self.supabase = supabase_client
            self.embedding_model = SentenceTransformer(settings.EMBEDDING_MODEL_NAME)
            logger.info("VectorService initialized with Supabase pgvector.")
        except Exception as e:
            logger.error(f"Failed to initialize VectorService: {e}", exc_info=True)
            raise

    def query(self, query_text: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Performs a semantic search query against the vector collection in Supabase.

        Args:
            query_text: The user's query string.
            top_k: The number of top results to return.

        Returns:
            A list of dictionaries, where each dictionary contains the
            retrieved document, its metadata, and distance score.
        """
        try:
            if not self.supabase:
                logger.error("Supabase client is not initialized in VectorService.")
                return []

            # Generate query embedding
            query_embedding = self.embedding_model.encode([query_text], show_progress_bar=False)[0].tolist()

            # Format the embedding for Supabase RPC
            # pgvector expects a string like '[0.1, 0.2, ...]'
            embedding_str = f"[{','.join(map(str, query_embedding))}]"

            # Call the match_document_chunks RPC function
            response = self.supabase.rpc(
                "match_document_chunks",
                {
                    "query_embedding": embedding_str,
                    "match_threshold": 0.0, # We rely on LIMIT instead
                    "match_count": top_k
                }
            ).execute()

            results = response.data
            
            formatted_results = []
            for item in results:
                formatted_results.append({
                    "id": item["id"],
                    "document": item["document"],
                    "metadata": item["metadata"],
                    "distance": item["similarity"]  # Higher similarity means lower distance conceptually
                })

            return formatted_results

        except Exception as e:
            logger.error(f"Failed to query Supabase pgvector: {e}", exc_info=True)
            return []

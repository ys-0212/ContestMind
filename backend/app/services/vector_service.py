# d:\Project\ContestMind\backend\app\services\vector_service.py
import logging
from typing import List, Dict, Any
from fastembed import TextEmbedding
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
            # Initialize fastembed TextEmbedding instead of sentence-transformers
            # fastembed automatically loads the ONNX version of the model, which uses ~50MB RAM instead of PyTorch's 400MB!
            self.embedding_model = TextEmbedding(model_name=f"sentence-transformers/{settings.EMBEDDING_MODEL_NAME}")
            logger.info("VectorService initialized with fastembed and Supabase pgvector.")
        except Exception as e:
            logger.error(f"Failed to initialize VectorService: {e}", exc_info=True)
            raise

    def query(self, query_text: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Performs a semantic search query against the vector collection in Supabase.
        """
        try:
            if not self.supabase:
                logger.error("Supabase client is not initialized in VectorService.")
                return []

            # Generate query embedding using fastembed
            # fastembed returns a generator, so we wrap in list()
            embeddings_generator = self.embedding_model.embed([query_text])
            query_embedding = list(embeddings_generator)[0].tolist()

            # Format the embedding for Supabase RPC
            embedding_str = f"[{','.join(map(str, query_embedding))}]"

            # Call the match_document_chunks RPC function
            response = self.supabase.rpc(
                "match_document_chunks",
                {
                    "query_embedding": embedding_str,
                    "match_threshold": 0.0, 
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
                    "distance": item["similarity"]
                })

            return formatted_results

        except Exception as e:
            logger.error(f"Failed to query Supabase pgvector: {e}", exc_info=True)
            return []

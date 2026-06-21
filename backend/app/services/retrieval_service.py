import logging
import re
import time
from typing import List

from app.core.utils import ttl_cache
from app.services.vector_service import VectorService
from ..schemas.retrieval import SearchResult

logger = logging.getLogger(__name__)

class RetrievalService:
    def __init__(self, chroma_service: VectorService):
        self.chroma_service = chroma_service

    def _format_results(self, raw_results: List[dict]) -> List[SearchResult]:
        formatted = []
        for res in raw_results:
            metadata = res.get("metadata", {})
            # Convert Chroma's L2 distance to cosine similarity.
            # all-MiniLM-L6-v2 produces unit-normalized vectors, so the correct
            # mapping is: cosine_sim = 1 - L2^2 / 2  (ranges 0 to 2 for unit vectors)
            distance = res.get("distance", 2.0)
            similarity = max(0.0, 1.0 - (distance ** 2) / 2.0)

            formatted.append(
                SearchResult(
                    problem_id=metadata.get("problem_id", ""),
                    title=metadata.get("title", "Unknown Title"),
                    rating=metadata.get("rating"),
                    tags=metadata.get("tags", []),
                    url=metadata.get("url", ""),
                    similarity_score=round(similarity, 4),
                    preview=res.get("document", "")[:250] + "..."
                )
            )
        return formatted

    @ttl_cache(ttl_seconds=3600) # Cache semantic searches for 1 hour
    def search(self, query: str, top_k: int) -> List[SearchResult]:
        # Sanitize query: remove extra whitespace
        clean_query = re.sub(r'\s+', ' ', query).strip()
        
        if not clean_query:
            return []

        logger.info(f"Performing search for query: '{clean_query}' with top_k={top_k}")
        
        start_time = time.time()
        try:
            raw_results = self.chroma_service.query(query_text=clean_query, top_k=top_k)
            elapsed = time.time() - start_time
            logger.info(f"Chroma DB query took {elapsed:.4f}s")
            return self._format_results(raw_results)
        except Exception as e:
            elapsed = time.time() - start_time
            logger.error(f"Retrieval failed after {elapsed:.4f}s: {e}")
            # Graceful fallback: return empty list instead of crashing
            return []

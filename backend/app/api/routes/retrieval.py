import logging
from fastapi import APIRouter, Depends, HTTPException

from app.schemas.retrieval import SearchRequest, SearchResponse
from app.services.retrieval_service import RetrievalService
from app.api.deps import get_retrieval_service

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/search", response_model=SearchResponse)
def search_problems(
    request: SearchRequest,
    retrieval_service: RetrievalService = Depends(get_retrieval_service)
):
    """
    Performs semantic search for competitive programming problems.
    """
    logger.info(f"Received search request with query: '{request.query}'")
    
    if not request.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty.")

    try:
        results = retrieval_service.search(query=request.query, top_k=request.top_k)
        return SearchResponse(
            query=request.query,
            results=results,
            count=len(results)
        )
    except Exception as e:
        logger.error(f"An unexpected error occurred during search for query: '{request.query}'", exc_info=True)
        raise HTTPException(status_code=500, detail="An internal error occurred during the search process.")

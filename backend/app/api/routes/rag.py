import logging
from fastapi import APIRouter, Depends, HTTPException

from app.schemas.rag import SimplifyRequest, SimplifyResponse
from app.services.rag_service import RAGService
from app.api.deps import get_rag_service

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/simplify", response_model=SimplifyResponse)
def simplify_editorial(
    request: SimplifyRequest,
    rag_service: RAGService = Depends(get_rag_service)
):
    """
    Generates a simplified editorial for a problem using RAG.
    """
    logger.info(f"Received simplification request for query: '{request.query}'")
    try:
        result = rag_service.simplify_editorial(query=request.query)
        return SimplifyResponse(
            query=request.query,
            **result
        )
    except Exception as e:
        logger.error(f"An unexpected error occurred during simplification for query: '{request.query}'", exc_info=True)
        raise HTTPException(status_code=500, detail="An internal error occurred during the RAG process.")

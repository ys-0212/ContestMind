"""
Health check endpoint.
- A simple route to verify that the API is running.
"""
from fastapi import APIRouter

router = APIRouter()

@router.get("/", status_code=200)
def health_check():
    """
    Health check endpoint.
    """
    return {"status": "ok"}

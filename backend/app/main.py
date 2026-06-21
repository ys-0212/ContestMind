"""
Main application entry point.
- Initializes the FastAPI app.
- Sets up middleware (CORS).
- Includes API routers.
"""
import logging
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import time
from collections import defaultdict

from app.api.api import api_router
from app.core.config import settings

import torch
torch.set_num_threads(1) # CRITICAL: Saves massive memory on CPU-only free tier deployments

# Configure logging
logging.basicConfig(level=settings.LOGGING_LEVEL)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# Set up CORS middleware
if settings.BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# --- 1. Centralized Error Handling ---
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception at {request.url.path}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "An internal server error occurred. Please try again later."},
    )

# --- 2. Request Logging Middleware & Simple Rate Limiting ---
# Very simple in-memory rate limiter (max 60 requests per minute per IP)
rate_limit_records = defaultdict(list)
RATE_LIMIT_MAX = 60
RATE_LIMIT_WINDOW = 60

@app.middleware("http")
async def log_and_limit_requests(request: Request, call_next):
    client_ip = request.client.host if request.client else "unknown"
    path = request.url.path

    # Rate limiting
    now = time.time()
    rate_limit_records[client_ip] = [t for t in rate_limit_records[client_ip] if now - t < RATE_LIMIT_WINDOW]
    if len(rate_limit_records[client_ip]) >= RATE_LIMIT_MAX:
        logger.warning(f"Rate limit exceeded for IP: {client_ip}")
        return JSONResponse(status_code=429, content={"detail": "Too Many Requests"})
    rate_limit_records[client_ip].append(now)

    # Request Logging
    start_time = time.time()
    logger.info(f"Incoming Request: {request.method} {path} from {client_ip}")
    
    try:
        response = await call_next(request)
        process_time = time.time() - start_time
        logger.info(f"Completed Request: {request.method} {path} - Status: {response.status_code} - Latency: {process_time:.4f}s")
        # Add latency header
        response.headers["X-Process-Time"] = str(process_time)
        return response
    except Exception as e:
        process_time = time.time() - start_time
        logger.error(f"Failed Request: {request.method} {path} - Latency: {process_time:.4f}s - Error: {e}")
        raise e

# Include the main API router
app.include_router(api_router, prefix=settings.API_V1_STR)

@app.on_event("startup")
async def startup_event():
    """
    Actions to perform on application startup.
    - e.g., connect to databases, load ML models.
    """
    logger.info("Application startup...")
    # In the future, you might connect to Supabase/ChromaDB here
    pass

@app.on_event("shutdown")
async def shutdown_event():
    """
    Actions to perform on application shutdown.
    - e.g., disconnect from databases.
    """
    logger.info("Application shutdown...")
    pass

#!/bin/bash
# ==============================================================================
# ContestMind Production Startup Script
# Run this on your production server (e.g. AWS, Render, Railway)
# ==============================================================================

# Ensure the script stops if any command fails
set -e

echo "Starting ContestMind Backend in Production Mode..."

# Run Gunicorn as the process manager.
# -w 4: 4 worker processes (scales to handle many concurrent users)
# -k uvicorn.workers.UvicornWorker: Instructs Gunicorn to use FastAPI's ASGI async workers
# --bind 0.0.0.0:8000: Bind to all IP addresses on port 8000
# --timeout 120: Allow 120 seconds for long ML model executions or LLM generation

gunicorn app.main:app \
    --workers 1 \
    --worker-class uvicorn.workers.UvicornWorker \
    --bind 0.0.0.0:8000 \
    --timeout 120 \
    --access-logfile - \
    --error-logfile -

"""
API route definitions.
- Includes routers from different modules (e.g., health, problems, llm).
- Centralizes all API endpoints.
"""
from fastapi import APIRouter
from app.api.routes import health, retrieval, rag, problems, llm, analytics, recommendations, attempts, profiles, contest_intelligence, hints, probability, chat, history, execute

api_router = APIRouter()
api_router.include_router(health.router, prefix="/health", tags=["health"])
api_router.include_router(retrieval.router, prefix="/retrieval", tags=["retrieval"])
api_router.include_router(rag.router, prefix="/rag", tags=["rag"])
api_router.include_router(problems.router, prefix="/problems", tags=["problems"])
api_router.include_router(llm.router, prefix="/llm", tags=["llm"])
api_router.include_router(analytics.router, prefix="/analytics", tags=["analytics"])
api_router.include_router(recommendations.router, prefix="/recommendations", tags=["recommendations"])
api_router.include_router(attempts.router, prefix="/attempts", tags=["attempts"])
api_router.include_router(profiles.router, prefix="/profiles", tags=["profiles"])
api_router.include_router(contest_intelligence.router, prefix="/contest-intelligence", tags=["contest-intelligence"])
api_router.include_router(hints.router, prefix="/hints", tags=["hints"])
api_router.include_router(probability.router, prefix="/probability", tags=["probability"])
api_router.include_router(chat.router, prefix="/chat", tags=["chat"])
api_router.include_router(history.router, prefix="/history", tags=["history"])
api_router.include_router(execute.router, prefix="/execute", tags=["execute"])

# Future routers to be added here:
# api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
# api_router.include_router(problems.router, prefix="/problems", tags=["problems"])
# api_router.include_router(retrieval.router, prefix="/retrieval", tags=["retrieval"])
# api_router.include_router(llm.router, prefix="/llm", tags=["llm"])
# api_router.include_router(analytics.router, prefix="/analytics", tags=["analytics"])
# api_router.include_router(recommend.router, prefix="/recommend", tags=["recommend"])
# api_router.include_-router(predict.router, prefix="/predict", tags=["predict"])

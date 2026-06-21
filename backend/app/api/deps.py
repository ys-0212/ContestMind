"""
Dependency injection for services.

Singleton instances are created once at startup and reused across all requests.
The LLM provider is selected via LLM_PROVIDER in config / .env.
"""

from app.services.vector_service import VectorService
from app.services.retrieval_service import RetrievalService
from app.services.llm.factory import create_llm_service
from app.services.llm.base import BaseLLMService
from app.services.rag_service import RAGService
from app.services.problem_service import ProblemService
from app.services.hint_service import HintService
from app.services.codeforces_service import CodeforcesService
from app.services.analytics_service import AnalyticsService
from app.services.probability_service import ProbabilityService
from app.services.recommendation_service import RecommendationService
from app.services.attempt_service import AttemptService
from app.services.profile_service import ProfileService
from app.services.contest_intelligence_service import ContestIntelligenceService
from supabase import create_client, Client
from app.core.config import settings

# Global Supabase Client
supabase_client: Client | None = None
if settings.SUPABASE_URL and settings.SUPABASE_KEY:
    supabase_client = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)

# Singletons
vector_service_instance = VectorService(supabase_client=supabase_client)
retrieval_service_instance = RetrievalService(chroma_service=vector_service_instance)
llm_service_instance: BaseLLMService = create_llm_service()
rag_service_instance = RAGService(
    retrieval_service=retrieval_service_instance,
    llm_service=llm_service_instance,
)
problem_service_instance = ProblemService(supabase_client=supabase_client)

codeforces_service_instance = CodeforcesService()
analytics_service_instance = AnalyticsService(
    codeforces_service=codeforces_service_instance,
    llm_service=llm_service_instance
)
attempt_service_instance = AttemptService()
hint_service_instance = HintService(
    problem_service=problem_service_instance,
    llm_service=llm_service_instance,
    chroma_service=vector_service_instance,
)
profile_service_instance = ProfileService(
    codeforces_service=codeforces_service_instance,
    analytics_service=analytics_service_instance,
    attempt_service=attempt_service_instance
)
probability_service_instance = ProbabilityService(
    profile_service=profile_service_instance,
    problem_service=problem_service_instance,
    llm_service=llm_service_instance
)

recommendation_service_instance = RecommendationService(
    problem_service=problem_service_instance,
    codeforces_service=codeforces_service_instance,
    profile_service=profile_service_instance,
    probability_service=probability_service_instance,
    llm_service=llm_service_instance
)
contest_intelligence_service_instance = ContestIntelligenceService(
    codeforces_service=codeforces_service_instance,
    llm_service=llm_service_instance
)
from app.services.chat_service import ChatService

chat_service_instance = ChatService(
    chroma_service=vector_service_instance,
    llm_service=llm_service_instance,
    supabase_client=supabase_client
)

def get_chat_service() -> ChatService:
    return chat_service_instance

def get_chroma_service() -> VectorService:
    return vector_service_instance

def get_retrieval_service() -> RetrievalService:
    return retrieval_service_instance

def get_llm_service() -> BaseLLMService:
    return llm_service_instance

def get_rag_service() -> RAGService:
    return rag_service_instance

def get_problem_service() -> ProblemService:
    return problem_service_instance

def get_codeforces_service() -> CodeforcesService:
    return codeforces_service_instance

def get_analytics_service() -> AnalyticsService:
    return analytics_service_instance

def get_probability_service() -> ProbabilityService:
    return probability_service_instance

def get_recommendation_service() -> RecommendationService:
    return recommendation_service_instance

def get_attempt_service() -> AttemptService:
    return attempt_service_instance

def get_hint_service() -> HintService:
    return hint_service_instance

def get_profile_service() -> ProfileService:
    return profile_service_instance

def get_contest_intelligence_service() -> ContestIntelligenceService:
    return contest_intelligence_service_instance

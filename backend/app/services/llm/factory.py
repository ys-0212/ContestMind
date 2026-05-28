import logging
from app.core.config import settings
from .base import BaseLLMService

logger = logging.getLogger(__name__)


def create_llm_service() -> BaseLLMService:
    """
    Returns the configured LLM provider instance.
    Add new providers here as elif branches when needed.
    """
    provider = settings.LLM_PROVIDER.lower()

    if provider == "groq":
        from .groq_service import GroqService
        return GroqService()

    raise ValueError(
        f"Unknown LLM_PROVIDER '{provider}'. "
        f"Supported providers: groq"
    )

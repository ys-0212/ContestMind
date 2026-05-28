import logging
import time
from groq import Groq, RateLimitError, APITimeoutError, APIStatusError, APIConnectionError

from app.core.config import settings
from .base import BaseLLMService

logger = logging.getLogger(__name__)

MAX_RETRIES = 2
DEFAULT_RETRY_DELAY = 60  # seconds


class GroqService(BaseLLMService):
    def __init__(self):
        if not settings.GROQ_API_KEY:
            raise ValueError("GROQ_API_KEY is not configured in .env")

        self.client = Groq(api_key=settings.GROQ_API_KEY)
        self.model = settings.GROQ_MODEL
        logger.info(f"GroqService initialized with model: {self.model}")

    def generate_text(self, prompt: str) -> str:
        for attempt in range(MAX_RETRIES + 1):
            try:
                logger.info(f"Sending request to Groq API (attempt {attempt + 1}/{MAX_RETRIES + 1})...")
                start_time = time.time()
                completion = self.client.chat.completions.create(
                    model=self.model,
                    messages=[{"role": "user", "content": prompt}],
                    timeout=settings.LLM_REQUEST_TIMEOUT,
                )
                elapsed = time.time() - start_time
                text = completion.choices[0].message.content
                logger.info(f"Successfully received response from Groq API in {elapsed:.4f}s.")
                return text or "Failed to generate response."

            except RateLimitError as e:
                retry_after = getattr(e, "retry_after", None) or DEFAULT_RETRY_DELAY
                if attempt < MAX_RETRIES:
                    logger.warning(
                        f"Groq rate limit hit (attempt {attempt + 1}). "
                        f"Retrying in {retry_after}s..."
                    )
                    time.sleep(float(retry_after))
                else:
                    logger.error("Groq rate limit exceeded after all retries.")
                    return "The AI service is temporarily rate-limited. Please try again in a moment."

            except APITimeoutError:
                if attempt < MAX_RETRIES:
                    logger.warning(f"Groq request timed out (attempt {attempt + 1}). Retrying...")
                    time.sleep(5)
                else:
                    logger.error("Groq request timed out after all retries.")
                    return "The AI service timed out. Please try again."

            except APIConnectionError as e:
                logger.error(f"Groq connection error: {e}")
                return "Could not connect to the AI service. Please check your network."

            except APIStatusError as e:
                logger.error(f"Groq API error {e.status_code}: {e.message}")
                return f"AI service returned an error ({e.status_code}). Please try again."

            except Exception as e:
                logger.error(f"Unexpected Groq error: {e}", exc_info=True)
                return "An unexpected error occurred while generating the response."

        return "Failed to generate response after retries."

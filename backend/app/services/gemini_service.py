import re
import time
import logging
from google import genai
from google.genai import errors as genai_errors

from app.core.config import settings

logger = logging.getLogger(__name__)

MAX_RETRIES = 2
DEFAULT_RETRY_DELAY = 60  # seconds


def _parse_retry_delay(error: Exception) -> float:
    match = re.search(r"retry in (\d+(?:\.\d+)?)s", str(error), re.IGNORECASE)
    if match:
        return float(match.group(1)) + 1.0
    return DEFAULT_RETRY_DELAY


class GeminiService:
    def __init__(self):
        if not settings.GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY is not configured.")

        self.client = genai.Client(
            api_key=settings.GEMINI_API_KEY,
            http_options={"api_version": "v1"},
        )
        self.model = settings.GEMINI_MODEL
        logger.info(f"GeminiService initialized with model: {self.model}")

    def generate_text(self, prompt: str) -> str:
        for attempt in range(MAX_RETRIES + 1):
            try:
                logger.info(f"Sending request to Gemini API (attempt {attempt + 1}/{MAX_RETRIES + 1})...")
                response = self.client.models.generate_content(
                    model=self.model,
                    contents=prompt,
                )
                logger.info("Successfully received response from Gemini API.")

                if response and response.text:
                    return response.text

                logger.warning("Gemini API returned an empty response.")
                return "Failed to generate response."

            except genai_errors.ClientError as e:
                # 429 — rate limit or quota exceeded
                if e.code == 429:
                    delay = _parse_retry_delay(e)
                    if attempt < MAX_RETRIES:
                        logger.warning(
                            f"Gemini quota exceeded (attempt {attempt + 1}). "
                            f"Retrying in {delay:.0f}s..."
                        )
                        time.sleep(delay)
                    else:
                        logger.error(
                            f"Gemini quota exceeded after {MAX_RETRIES + 1} attempts. "
                            f"Daily free-tier limit hit — try again tomorrow or use a new API key."
                        )
                        return (
                            "The AI service is temporarily unavailable due to rate limits. "
                            "Please try again in a few minutes."
                        )
                # 404 — wrong model name
                elif e.code == 404:
                    logger.error(f"Model '{self.model}' not found: {e}")
                    return f"Configured model '{self.model}' is unavailable. Check GEMINI_MODEL in .env."
                else:
                    logger.error(f"Gemini client error {e.code}: {e}", exc_info=True)
                    return "An error occurred while contacting the AI service."

            except Exception as e:
                logger.error(f"Unexpected Gemini API error: {e}", exc_info=True)
                return "An unexpected error occurred while generating the response."

        return "Failed to generate response after retries."

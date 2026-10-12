# d:\Project\ContestMind\backend\app\core\config.py
import os
from pathlib import Path
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict

# All paths are now relative to the 'backend' directory root.
BACKEND_ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(BACKEND_ROOT / ".env"),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # --- Core Settings ---
    PROJECT_NAME: str = "ContestMind"
    ENVIRONMENT: str = "development"
    API_V1_STR: str = "/api/v1"
    LOGGING_LEVEL: str = "INFO"

    # --- LLM Provider ---
    LLM_PROVIDER: str = "groq"          # options: groq
    LLM_REQUEST_TIMEOUT: int = 60

    # --- Groq Settings ---
    GROQ_API_KEY: Optional[str] = None
    GROQ_MODEL: str = "llama-3.3-70b-versatile"

    # --- Gemini Settings (kept for reference, not active) ---
    GEMINI_MODEL: str = "gemini-2.0-flash"
    GEMINI_REQUEST_TIMEOUT: int = 60
    GEMINI_API_KEY: Optional[str] = None

    # --- Supabase (Optional for preprocessing) ---
    SUPABASE_URL: Optional[str] = None
    SUPABASE_KEY: Optional[str] = None
    SUPABASE_JWT_SECRET: Optional[str] = None

    # --- ChromaDB/Embedding Settings ---
    CHROMA_PERSIST_DIR: str = "data/chroma"
    CHROMA_COLLECTION_NAME: str = "contestmind"
    EMBEDDING_MODEL_NAME: str = "sentence-transformers/all-MiniLM-L6-v2"

    # --- Data Paths (Relative to backend root) ---
    DATA_DIR: Path = BACKEND_ROOT / "data"
    RAW_DATA_DIR: Path = DATA_DIR / "raw"
    PROCESSED_DATA_DIR: Path = DATA_DIR / "processed"
    CHUNKS_DATA_DIR: Path = DATA_DIR / "chunks"

    # --- CORS Settings ---
    BACKEND_CORS_ORIGINS: list[str] | str = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
        "https://contest-mind.vercel.app",
    ]
    CORS_ALLOW_CREDENTIALS: bool = False

    @property
    def cors_origins(self) -> list[str]:
        raw = self.BACKEND_CORS_ORIGINS
        if isinstance(raw, str):
            raw = raw.strip()
            if raw.startswith("[") and raw.endswith("]"):
                import json
                try:
                    parsed = json.loads(raw)
                    if isinstance(parsed, list):
                        return [str(o).strip().rstrip("/") for o in parsed if str(o).strip()]
                except Exception:
                    pass
            return [o.strip().rstrip("/") for o in raw.split(",") if o.strip()]
        elif isinstance(raw, (list, tuple, set)):
            return [str(o).strip().rstrip("/") for o in raw if str(o).strip()]
        return []

settings = Settings()

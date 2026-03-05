"""
config.py – Central configuration for Researcho backend.
All values are read from environment variables (or a .env file).
Uses Google Gemini API for fast, free LLM inference.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Literal
from pathlib import Path

# Always resolve .env relative to this file, regardless of CWD
_ENV_FILE = Path(__file__).parent / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(_ENV_FILE),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # ── LLM (Google Gemini) ──────────────────────────────────────────────────
    LLM_MODEL: str = "models/gemini-1.5-flash"   # free tier model
    LLM_MAX_NEW_TOKENS: int = 2048
    LLM_TEMPERATURE: float = 0.1
    GEMINI_API_KEY: str = ""              # set in .env – get free key at aistudio.google.com

    # ── Embeddings (sentence-transformers – local) ───────────────────────────
    EMBED_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"
    EMBED_DIM: int = 384

    # ── Qdrant ───────────────────────────────────────────────────────────────
    QDRANT_MODE: Literal["memory", "local"] = "memory"
    QDRANT_URL: str = "http://localhost:6333"
    QDRANT_API_KEY: str = ""

    # ── Web Search & Scraping ────────────────────────────────────────────────
    WEB_SEARCH_ENABLED: bool = True
    WEB_SEARCH_MAX_RESULTS: int = 5
    WEB_SCRAPE_MAX_CHARS: int = 3000

    # ── App ──────────────────────────────────────────────────────────────────
    APP_HOST: str = "0.0.0.0"
    APP_PORT: int = 8000
    FRONTEND_DIR: str = "../frontend"
    ALLOWED_ORIGINS: str = "*"


settings = Settings()

# langchain-google-genai reads GOOGLE_API_KEY env var during Pydantic validation.
# Set it here so it's available before any LLM is instantiated.
import os as _os
if settings.GEMINI_API_KEY:
    _os.environ.setdefault("GOOGLE_API_KEY", settings.GEMINI_API_KEY)


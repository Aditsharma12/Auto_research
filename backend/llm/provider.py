"""
llm/provider.py – Gemini via langchain-google-genai.
Uses ChatGoogleGenerativeAI which handles auth via GOOGLE_API_KEY env var.
"""

from __future__ import annotations
import logging
import os

from langchain_google_genai import ChatGoogleGenerativeAI

from config import settings

logger = logging.getLogger(__name__)

# Set GOOGLE_API_KEY env var so langchain-google-genai can pick it up
os.environ["GOOGLE_API_KEY"] = settings.GEMINI_API_KEY

# ── Shared LLM cache ──────────────────────────────────────────────────────────
_llm_cache: dict[float, ChatGoogleGenerativeAI] = {}


def get_llm(temperature: float | None = None) -> ChatGoogleGenerativeAI:
    """Return a cached LangChain-compatible Gemini LLM."""
    temp = temperature if temperature is not None else settings.LLM_TEMPERATURE

    if temp not in _llm_cache:
        # Strip "models/" prefix if present
        model_name = settings.LLM_MODEL
        if model_name.startswith("models/"):
            model_name = model_name[len("models/"):]

        _llm_cache[temp] = ChatGoogleGenerativeAI(
            model=model_name,
            temperature=temp,
        )
        logger.info(f"Created Gemini LLM: {model_name} (temp={temp})")

    return _llm_cache[temp]


def estimate_cost(model: str, input_tokens: int, output_tokens: int) -> float:
    """Gemini free tier – zero cost within quota."""
    return 0.0

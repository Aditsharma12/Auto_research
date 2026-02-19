"""
llm/embedder.py – Local embeddings via sentence-transformers (CPU, no API key needed).
"""

from functools import lru_cache

from langchain_huggingface import HuggingFaceEmbeddings

from config import settings


@lru_cache(maxsize=1)
def get_embedder() -> HuggingFaceEmbeddings:
    """
    Return a cached sentence-transformers embedding model.
    Downloads on first use, cached in ~/.cache/huggingface afterward.
    """
    return HuggingFaceEmbeddings(
        model_name=settings.EMBED_MODEL,
        model_kwargs={"device": "cpu"},
        encode_kwargs={"normalize_embeddings": True},
    )

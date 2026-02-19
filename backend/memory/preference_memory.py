"""
memory/preference_memory.py – Stores and retrieves per-user preferences in Qdrant.
"""

import json
import uuid
from datetime import datetime

from qdrant_client.models import PointStruct, Filter, FieldCondition, MatchValue

from memory.qdrant_client import get_client, COLLECTION_PREFERENCES
from llm.embedder import get_embedder

_embedder = None


def _get_embedder():
    global _embedder
    if _embedder is None:
        _embedder = get_embedder()
    return _embedder


DEFAULT_PREFERENCES = {
    "prefers_code_examples": False,
    "expertise_level": "intermediate",
    "preferred_answer_length": "detailed",
    # ── E-Commerce domain preferences ──────────────────────────
    "focus_area": "general",           # margins | reviews | pricing | competitor_gap | general
    "business_role": "general",        # product_manager | analyst | founder | general
    "primary_metric": "general",       # revenue | conversion | return_rate | margin | general
}


def load_preferences(user_id: str) -> dict:
    """Load user preferences from Qdrant. Returns defaults if not found."""
    client = get_client()
    try:
        results = client.scroll(
            collection_name=COLLECTION_PREFERENCES,
            scroll_filter=Filter(
                must=[FieldCondition(key="user_id", match=MatchValue(value=user_id))]
            ),
            limit=1,
            with_payload=True,
            with_vectors=False,
        )
        points = results[0]
        if points:
            payload = points[0].payload or {}
            return {
                "prefers_code_examples": payload.get("prefers_code_examples", False),
                "expertise_level": payload.get("expertise_level", "intermediate"),
                "preferred_answer_length": payload.get("preferred_answer_length", "detailed"),
                "focus_area": payload.get("focus_area", "general"),
                "business_role": payload.get("business_role", "general"),
                "primary_metric": payload.get("primary_metric", "general"),
            }
    except Exception:
        pass
    return dict(DEFAULT_PREFERENCES)


def save_preferences(user_id: str, preferences: dict) -> None:
    """Upsert user preferences in Qdrant."""
    client = get_client()
    embedder = _get_embedder()

    # Embed a stable text representation of the user_id for indexing
    try:
        vector = embedder.embed_query(f"preferences for user {user_id}")
    except Exception:
        vector = [0.0] * 768   # fallback zero vector

    payload = {
        "user_id": user_id,
        "last_updated": datetime.utcnow().isoformat(),
        **preferences,
    }

    # Delete existing record for this user first
    try:
        client.delete(
            collection_name=COLLECTION_PREFERENCES,
            points_selector=Filter(
                must=[FieldCondition(key="user_id", match=MatchValue(value=user_id))]
            ),
        )
    except Exception:
        pass

    client.upsert(
        collection_name=COLLECTION_PREFERENCES,
        points=[PointStruct(
            id=str(uuid.uuid5(uuid.NAMESPACE_DNS, user_id)),
            vector=vector,
            payload=payload,
        )],
    )

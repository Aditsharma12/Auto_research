"""
memory/history_memory.py – Stores and retrieves research session history.
"""

import uuid
from datetime import datetime
from typing import List

from qdrant_client.models import PointStruct, Filter, FieldCondition, MatchValue, SearchRequest

from memory.qdrant_client import get_client, COLLECTION_HISTORY
from llm.embedder import get_embedder

_embedder = None


def _get_embedder():
    global _embedder
    if _embedder is None:
        _embedder = get_embedder()
    return _embedder


def save_research(
    user_id: str,
    query: str,
    mode: str,
    summary: str,
    key_findings: str,
) -> None:
    """Persist a completed research session to Qdrant history."""
    client = get_client()
    embedder = _get_embedder()

    try:
        vector = embedder.embed_query(query)
    except Exception:
        vector = [0.0] * 768

    point_id = str(uuid.uuid4())
    payload = {
        "user_id": user_id,
        "query": query,
        "mode": mode,
        "summary": summary,
        "key_findings": key_findings,
        "timestamp": datetime.utcnow().isoformat(),
    }

    client.upsert(
        collection_name=COLLECTION_HISTORY,
        points=[PointStruct(id=point_id, vector=vector, payload=payload)],
    )


def search_history(query: str, user_id: str, top_k: int = 3) -> List[dict]:
    """Retrieve semantically similar past research for this user."""
    client = get_client()
    embedder = _get_embedder()

    try:
        vector = embedder.embed_query(query)
    except Exception:
        return []

    try:
        results = client.search(
            collection_name=COLLECTION_HISTORY,
            query_vector=vector,
            query_filter=Filter(
                must=[FieldCondition(key="user_id", match=MatchValue(value=user_id))]
            ),
            limit=top_k,
            with_payload=True,
        )
        return [
            {
                "query": r.payload.get("query", ""),
                "summary": r.payload.get("summary", ""),
                "key_findings": r.payload.get("key_findings", ""),
                "mode": r.payload.get("mode", ""),
                "timestamp": r.payload.get("timestamp", ""),
                "score": r.score,
            }
            for r in results
        ]
    except Exception:
        return []

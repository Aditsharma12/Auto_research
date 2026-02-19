"""
memory/qdrant_client.py – Qdrant client factory.
Supports in-memory (no install needed) and local server modes.
"""

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams

from config import settings

_client: QdrantClient | None = None

# Collection names
COLLECTION_PREFERENCES = "user_preferences"
COLLECTION_HISTORY = "research_history"
COLLECTION_DOCUMENTS = "documents"


def get_client() -> QdrantClient:
    """Return (or create) the singleton Qdrant client."""
    global _client
    if _client is None:
        if settings.QDRANT_MODE == "memory":
            _client = QdrantClient(":memory:")
        else:
            _client = QdrantClient(
                url=settings.QDRANT_URL,
                api_key=settings.QDRANT_API_KEY or None,
            )
        _ensure_collections(_client)
    return _client


def _ensure_collections(client: QdrantClient) -> None:
    """Create required collections if they don't exist."""
    dim = settings.EMBED_DIM

    existing = {c.name for c in client.get_collections().collections}

    for name in [COLLECTION_PREFERENCES, COLLECTION_HISTORY, COLLECTION_DOCUMENTS]:
        if name not in existing:
            client.create_collection(
                collection_name=name,
                vectors_config=VectorParams(size=dim, distance=Distance.COSINE),
            )

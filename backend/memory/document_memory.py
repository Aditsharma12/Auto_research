"""
memory/document_memory.py – Indexes and searches technical documents in Qdrant.
"""

import uuid
from typing import List

from qdrant_client.models import PointStruct

from memory.qdrant_client import get_client, COLLECTION_DOCUMENTS
from llm.embedder import get_embedder

_embedder = None


def _get_embedder():
    global _embedder
    if _embedder is None:
        _embedder = get_embedder()
    return _embedder


def index_document(text: str, source: str, metadata: dict | None = None) -> None:
    """
    Index a single text chunk into the document collection.

    Args:
        text: The chunk text to embed and store.
        source: The source URL, filename, or label.
        metadata: Optional extra metadata to store in payload.
    """
    client = get_client()
    embedder = _get_embedder()

    try:
        vector = embedder.embed_query(text)
    except Exception:
        return   # silently skip on embedding error

    payload = {
        "text": text,
        "source": source,
        **(metadata or {}),
    }

    client.upsert(
        collection_name=COLLECTION_DOCUMENTS,
        points=[PointStruct(
            id=str(uuid.uuid4()),
            vector=vector,
            payload=payload,
        )],
    )


def index_documents_bulk(chunks: List[dict]) -> None:
    """
    Index a list of document chunks.

    Args:
        chunks: List of {"text": str, "source": str, "metadata": dict} dicts.
    """
    for chunk in chunks:
        index_document(
            text=chunk["text"],
            source=chunk.get("source", "unknown"),
            metadata=chunk.get("metadata"),
        )


def search_documents(query: str, top_k: int = 5) -> List[dict]:
    """
    Semantic search over the document index.

    Returns:
        List of {"text", "source", "score"} dicts sorted by relevance.
    """
    client = get_client()
    embedder = _get_embedder()

    try:
        vector = embedder.embed_query(query)
    except Exception:
        return []

    try:
        results = client.search(
            collection_name=COLLECTION_DOCUMENTS,
            query_vector=vector,
            limit=top_k,
            with_payload=True,
        )
        return [
            {
                "text": r.payload.get("text", ""),
                "source": r.payload.get("source", ""),
                "score": round(r.score, 4),
            }
            for r in results
        ]
    except Exception:
        return []

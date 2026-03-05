"""
graph/nodes/auto_indexer.py – Automatically indexes scraped web content into Qdrant.
Chunks the scraped text and indexes each chunk so the retriever can
immediately use the freshly ingested web data.
"""

import logging
from graph.state import ResearchState
from memory.document_memory import index_document
from memory.chunker import chunk_text

logger = logging.getLogger(__name__)


def auto_indexer_node(state: ResearchState) -> ResearchState:
    """
    Takes scraped web content, chunks it, and indexes into Qdrant.
    After this node, the retriever will find freshly indexed web data.
    """
    scraped_content = state.get("scraped_content", [])

    if not scraped_content:
        return state

    total_chunks = 0

    for item in scraped_content:
        url = item.get("url", "unknown")
        text = item.get("text", "")

        if not text:
            continue

        # Chunk the text for better embedding granularity
        chunks = chunk_text(text, chunk_size=500, overlap=100)

        for chunk in chunks:
            try:
                index_document(
                    text=chunk,
                    source=url,
                    metadata={
                        "type": "web_scrape",
                        "url": url,
                    },
                )
                total_chunks += 1
            except Exception as e:
                logger.warning(f"Failed to index chunk from {url}: {e}")

    logger.info(f"Auto-indexed {total_chunks} chunks from {len(scraped_content)} pages")
    return state

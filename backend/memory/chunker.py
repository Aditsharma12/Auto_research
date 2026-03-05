"""
memory/chunker.py – Text chunking utility for splitting scraped content
into embedding-friendly chunks for Qdrant indexing.
"""

from typing import List


def chunk_text(
    text: str,
    chunk_size: int = 500,
    overlap: int = 100,
) -> List[str]:
    """
    Split text into overlapping chunks.

    Args:
        text: The full text to chunk.
        chunk_size: Target size of each chunk in characters.
        overlap: Number of overlapping characters between consecutive chunks.

    Returns:
        List of text chunks.
    """
    if not text or not text.strip():
        return []

    text = text.strip()

    # If text fits in one chunk, return as-is
    if len(text) <= chunk_size:
        return [text]

    chunks: list[str] = []
    start = 0

    while start < len(text):
        end = start + chunk_size

        # Try to break at a sentence boundary (., !, ?) or newline
        if end < len(text):
            # Look backwards from 'end' for a good break point
            search_start = max(start + chunk_size // 2, start)
            best_break = end
            for i in range(end, search_start, -1):
                if text[i] in ".!?\n":
                    best_break = i + 1
                    break
            end = best_break

        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)

        # Move start forward, accounting for overlap
        start = end - overlap
        if start <= (end - chunk_size):
            # Prevent infinite loop
            start = end

    return chunks

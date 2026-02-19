"""
graph/nodes/confidence.py – Confidence estimation node.
Scores result confidence based on retrieval quality and source diversity.
"""

from graph.state import ResearchState


def confidence_node(state: ResearchState) -> ResearchState:
    """
    Estimate a 0.0–1.0 confidence score based on:
    - Number of retrieved chunks (more = better)
    - Average retrieval similarity score
    - Source diversity (different sources = better)
    - Presence of error (reduces confidence)
    """
    chunks = state.get("retrieved_chunks", [])
    error = state.get("error")

    score = 0.5  # baseline

    # ── Source count factor ──────────────────────────────────────
    n = len(chunks)
    if n >= 5:
        score += 0.20
    elif n >= 3:
        score += 0.12
    elif n >= 1:
        score += 0.05

    # ── Average similarity score factor ─────────────────────────
    if chunks:
        avg_sim = sum(c.get("score", 0.5) for c in chunks) / len(chunks)
        score += avg_sim * 0.20   # up to +0.2 from sim

    # ── Source diversity factor ──────────────────────────────────
    sources = {c.get("source", "") for c in chunks if c.get("source")}
    if len(sources) >= 3:
        score += 0.10
    elif len(sources) >= 2:
        score += 0.05

    # ── Error penalty ────────────────────────────────────────────
    if error:
        score -= 0.20

    # ── No retrieval penalty ─────────────────────────────────────
    if not chunks:
        score = 0.30   # knowledge-only, low confidence

    state["confidence"] = round(min(max(score, 0.0), 1.0), 2)
    return state

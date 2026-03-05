"""
state.py – Shared state schema for the LangGraph research graph.
Every node reads from and writes to this TypedDict.
"""

from typing import TypedDict, List, Optional, Literal


class ResearchState(TypedDict, total=False):
    # ── Input ────────────────────────────────────────────────────
    query: str                          # original user query
    mode: Literal["quick", "deep"]      # research mode
    user_id: str                        # user identifier for memory

    # ── Routing ─────────────────────────────────────────────────
    needs_clarification: bool           # set by clarification node

    # ── Clarification ────────────────────────────────────────────
    clarification_question: Optional[str]   # question to ask the user
    clarification_answer: Optional[str]     # user's answer (if provided)

    # ── Planning ─────────────────────────────────────────────────
    sub_questions: List[str]            # decomposed sub-questions (deep mode)

    # ── Retrieval ────────────────────────────────────────────────
    retrieved_chunks: List[dict]        # list of {text, source, score}
    past_research: List[dict]           # relevant past research from memory

    # ── Web Search & Scraping ────────────────────────────────────
    search_results: List[dict]          # raw search results [{title, url, snippet}]
    scraped_content: List[dict]         # scraped pages [{url, text}]
    web_sources: List[str]              # list of source URLs used

    # ── Reasoning ────────────────────────────────────────────────
    reasoning_notes: str                # intermediate reasoning trace
    review_analysis: Optional[str]      # structured review analysis from dedicated node

    # ── Output ──────────────────────────────────────────────────
    report: str                         # final structured Markdown report

    # ── Metrics ─────────────────────────────────────────────────
    confidence: float                   # 0.0 – 1.0
    input_tokens: int
    output_tokens: int
    latency: float                      # seconds
    estimated_cost: float               # USD

    # ── Error handling ───────────────────────────────────────────
    error: Optional[str]

    # ── User preferences (loaded from memory) ───────────────────
    prefers_code_examples: bool
    expertise_level: Literal["beginner", "intermediate", "advanced"]
    preferred_answer_length: Literal["short", "detailed"]

    # ── E-Commerce domain preferences ───────────────────────────
    focus_area: Literal["margins", "reviews", "pricing", "competitor_gap", "general"]
    business_role: Literal["product_manager", "analyst", "founder", "general"]
    primary_metric: Literal["revenue", "conversion", "return_rate", "margin", "general"]

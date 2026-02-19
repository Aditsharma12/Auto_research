"""
graph/nodes/cost_tracker.py – Token usage and cost estimation node.
"""

import time
from graph.state import ResearchState
from llm.provider import estimate_cost
from config import settings


# Module-level start time (rough, per-request timing set in main.py)
_REQUEST_START: dict[str, float] = {}


def cost_tracker_node(state: ResearchState) -> ResearchState:
    """
    Estimates token usage and cost for the completed research run.
    Token counts are heuristic (chars/4) when exact counts aren't available.
    """
    reasoning_notes = state.get("reasoning_notes", "")
    report = state.get("report", "")
    query = state.get("query", "")

    # Heuristic token counting (~4 chars per token)
    input_text = query + reasoning_notes
    output_text = report

    input_tokens = max(1, len(input_text) // 4)
    output_tokens = max(1, len(output_text) // 4)

    state["input_tokens"] = input_tokens
    state["output_tokens"] = output_tokens
    state["estimated_cost"] = estimate_cost(
        model=settings.LLM_MODEL,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
    )

    # Latency is set in main.py; if not set, use 0
    if "latency" not in state:
        state["latency"] = 0.0

    return state

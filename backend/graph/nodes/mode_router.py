"""
graph/nodes/mode_router.py – Routes the query to Quick or Deep mode path.
"""

from graph.state import ResearchState


def mode_router_node(state: ResearchState) -> ResearchState:
    """
    Route based on the requested mode.
    Sets defaults for user preference fields if not already loaded.
    """
    # Apply defaults for preference fields
    state.setdefault("prefers_code_examples", True)
    state.setdefault("expertise_level", "intermediate")
    state.setdefault("preferred_answer_length", "detailed")
    state.setdefault("sub_questions", [])
    state.setdefault("retrieved_chunks", [])
    state.setdefault("past_research", [])
    state.setdefault("reasoning_notes", "")
    state.setdefault("needs_clarification", False)
    state.setdefault("clarification_question", None)
    state.setdefault("clarification_answer", None)
    state.setdefault("error", None)
    state.setdefault("search_results", [])
    state.setdefault("scraped_content", [])
    state.setdefault("web_sources", [])

    return state


def route_by_mode(state: ResearchState) -> str:
    """
    Conditional edge function: decides next node after mode routing.
    Returns the name of the next node.
    """
    if state.get("mode") == "quick":
        return "retriever_quick"
    else:
        return "clarification"

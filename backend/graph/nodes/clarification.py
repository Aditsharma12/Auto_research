"""
graph/nodes/clarification.py – Detects query ambiguity and asks one clarifying question.
"""

from langchain_core.messages import SystemMessage, HumanMessage

from graph.state import ResearchState
from prompts.clarification import (
    CLARIFICATION_SYSTEM,
    CLARIFICATION_HUMAN,
    AMBIGUITY_KEYWORDS,
)
from llm.provider import get_llm


def clarification_node(state: ResearchState) -> ResearchState:
    """
    Checks if the query needs clarification.
    If yes, stores a clarification question.
    If clarification_answer is already present, skips.
    """
    # If user already answered the clarification, don't ask again
    if state.get("clarification_answer"):
        state["needs_clarification"] = False
        return state

    query = state["query"]
    llm = get_llm(temperature=0.0)

    try:
        response = llm.invoke([
            SystemMessage(content=CLARIFICATION_SYSTEM),
            HumanMessage(content=CLARIFICATION_HUMAN.format(query=query)),
        ])
        text = response.content.strip()

        if text.upper() == "CLEAR":
            state["needs_clarification"] = False
            state["clarification_question"] = None
        else:
            state["needs_clarification"] = True
            state["clarification_question"] = text

    except Exception as e:
        # On error, assume clear and continue
        state["needs_clarification"] = False
        state["error"] = f"Clarification node error: {str(e)}"

    return state


def route_after_clarification(state: ResearchState) -> str:
    """Conditional edge: if clarification needed, halt (API returns the question)."""
    if state.get("needs_clarification"):
        return "needs_clarification"
    return "planner"

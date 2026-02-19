"""
graph/nodes/synthesis.py – Generates the final structured research report.
"""

from langchain_core.messages import SystemMessage, HumanMessage

from graph.state import ResearchState
from prompts.synthesis import (
    SYNTHESIS_SYSTEM_DEEP, SYNTHESIS_HUMAN_DEEP,
    SYNTHESIS_SYSTEM_QUICK, SYNTHESIS_HUMAN_QUICK,
)
from llm.provider import get_llm


def synthesis_node(state: ResearchState) -> ResearchState:
    """
    Deep mode: synthesizes reasoning notes + past research into a structured report.
    """
    llm = get_llm(temperature=0.15)

    # Format past research summaries
    past_research_str = ""
    for pr in state.get("past_research", []):
        past_research_str += f"- **{pr.get('query', '')}**: {pr.get('summary', '')}\n"
    if not past_research_str:
        past_research_str = "No past research found."

    try:
        response = llm.invoke([
            SystemMessage(content=SYNTHESIS_SYSTEM_DEEP),
            HumanMessage(content=SYNTHESIS_HUMAN_DEEP.format(
                query=state["query"],
                reasoning_notes=state.get("reasoning_notes", ""),
                review_analysis=state.get("review_analysis", "No structured review analysis available."),
                past_research=past_research_str,
                expertise_level=state.get("expertise_level", "intermediate"),
                prefers_code_examples=state.get("prefers_code_examples", True),
                preferred_answer_length=state.get("preferred_answer_length", "detailed"),
                focus_area=state.get("focus_area", "general"),
                primary_metric=state.get("primary_metric", "general"),
            )),
        ])
        state["report"] = response.content.strip()

    except Exception as e:
        state["report"] = f"## Error\nSynthesis failed: {str(e)}"
        state["error"] = str(e)

    return state


def synthesis_quick_node(state: ResearchState) -> ResearchState:
    """
    Quick mode: single-pass synthesis directly from retrieved chunks.
    """
    llm = get_llm(temperature=0.1)

    chunks = state.get("retrieved_chunks", [])
    if chunks:
        context_str = "\n\n".join([
            f"[Source {i+1}]: {c.get('text', '')}"
            for i, c in enumerate(chunks)
        ])
    else:
        context_str = "No external context. Use pre-trained knowledge."

    try:
        response = llm.invoke([
            SystemMessage(content=SYNTHESIS_SYSTEM_QUICK),
            HumanMessage(content=SYNTHESIS_HUMAN_QUICK.format(
                query=state["query"],
                context=context_str,
                expertise_level=state.get("expertise_level", "intermediate"),
                focus_area=state.get("focus_area", "general"),
            )),
        ])
        state["report"] = response.content.strip()

    except Exception as e:
        state["report"] = f"## Error\nQuick synthesis failed: {str(e)}"
        state["error"] = str(e)

    return state

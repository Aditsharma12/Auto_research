"""
graph/nodes/planner.py – Decomposes a complex query into sub-questions.
"""

import re
from langchain_core.messages import SystemMessage, HumanMessage

from graph.state import ResearchState
from prompts.planner import PLANNER_SYSTEM, PLANNER_HUMAN
from llm.provider import get_llm


def planner_node(state: ResearchState) -> ResearchState:
    """
    Decomposes the query into 3-5 focused sub-questions for retrieval.
    In quick mode this is skipped — sub_questions defaults to [query].
    """
    query = state["query"]

    # If clarification answer was provided, enrich the query
    if state.get("clarification_answer"):
        query = f"{query}\n\nAdditional context: {state['clarification_answer']}"

    llm = get_llm(temperature=0.1)

    try:
        response = llm.invoke([
            SystemMessage(content=PLANNER_SYSTEM),
            HumanMessage(content=PLANNER_HUMAN.format(query=query)),
        ])
        raw = response.content.strip()

        # Parse numbered list  "1. ..." → list of strings
        sub_questions = []
        for line in raw.splitlines():
            line = line.strip()
            match = re.match(r"^\d+[\.\)]\s+(.+)", line)
            if match:
                sub_questions.append(match.group(1))

        if not sub_questions:
            # Fallback: use original query as single question
            sub_questions = [query]

        state["sub_questions"] = sub_questions[:5]   # cap at 5

    except Exception as e:
        state["sub_questions"] = [query]
        state["error"] = f"Planner node error: {str(e)}"

    return state

"""
graph/nodes/reasoning.py – Iterative reasoning over retrieved chunks.
"""

from langchain_core.messages import SystemMessage, HumanMessage

from graph.state import ResearchState
from prompts.reasoning import REASONING_SYSTEM, REASONING_HUMAN
from llm.provider import get_llm


def reasoning_node(state: ResearchState) -> ResearchState:
    """
    For each sub-question, perform LLM reasoning over retrieved context.
    Accumulates reasoning notes into state["reasoning_notes"].
    """
    sub_questions = state.get("sub_questions", [state["query"]])
    chunks = state.get("retrieved_chunks", [])
    expertise_level = state.get("expertise_level", "intermediate")

    llm = get_llm(temperature=0.1)
    all_notes: list[str] = []

    for idx, sq in enumerate(sub_questions):
        # Build context string from chunks relevant to this sub-question
        if chunks:
            context_parts = []
            for i, chunk in enumerate(chunks):
                src = chunk.get("source", "Unknown")
                text = chunk.get("text", "")
                score = chunk.get("score", 0.0)
                context_parts.append(f"[Source {i+1}] (relevance: {score:.2f}) from {src}:\n{text}")
            context_str = "\n\n".join(context_parts)
        else:
            context_str = "No external context retrieved. Use your pre-trained knowledge."

        try:
            response = llm.invoke([
                SystemMessage(content=REASONING_SYSTEM),
                HumanMessage(content=REASONING_HUMAN.format(
                    sub_question=sq,
                    context=context_str,
                    expertise_level=expertise_level,
                )),
            ])
            note = f"### Sub-question {idx + 1}: {sq}\n\n{response.content.strip()}"
            all_notes.append(note)

        except Exception as e:
            all_notes.append(f"### Sub-question {idx + 1}: {sq}\n\n[Error during reasoning: {e}]")

    return {"reasoning_notes": "\n\n---\n\n".join(all_notes)}

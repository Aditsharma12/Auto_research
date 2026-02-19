"""
graph/nodes/retriever.py – Semantic retrieval from Qdrant document store.
Used by both Quick and Deep mode paths.
"""

from graph.state import ResearchState
from memory.document_memory import search_documents
from memory.history_memory import search_history


def retriever_node(state: ResearchState) -> ResearchState:
    """
    Deep mode retriever:
    Retrieves top-k chunks for each sub-question, plus relevant past research.
    """
    sub_questions = state.get("sub_questions", [state["query"]])
    user_id = state.get("user_id", "anonymous")

    all_chunks: list[dict] = []
    seen_texts: set[str] = set()

    for sq in sub_questions:
        chunks = search_documents(query=sq, top_k=4)
        for chunk in chunks:
            key = chunk.get("text", "")[:100]
            if key not in seen_texts:
                seen_texts.add(key)
                all_chunks.append(chunk)

    state["retrieved_chunks"] = all_chunks

    # Also load relevant past research for this user
    past = search_history(query=state["query"], user_id=user_id, top_k=3)
    state["past_research"] = past

    return state


def retriever_quick_node(state: ResearchState) -> ResearchState:
    """
    Quick mode retriever:
    Single retrieval pass for the original query only.
    """
    query = state["query"]
    chunks = search_documents(query=query, top_k=5)
    state["retrieved_chunks"] = chunks
    state["past_research"] = []
    return state

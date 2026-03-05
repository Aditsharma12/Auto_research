"""
graph/orchestrator.py – Builds and compiles the LangGraph research graph.

Flow:
  Quick:   mode_router → web_search → web_scraper → auto_indexer
           → retriever_quick → synthesis_quick → cost_tracker → confidence → END
  Deep:    mode_router → clarification → [needs_clarification: END]
                       → planner → web_search → web_scraper → auto_indexer
                       → retriever → reasoning + review_analyzer
                       → synthesis → cost_tracker → confidence → END
"""

from langgraph.graph import StateGraph, END

from graph.state import ResearchState
from graph.nodes.mode_router import mode_router_node, route_by_mode
from graph.nodes.clarification import clarification_node, route_after_clarification
from graph.nodes.planner import planner_node
from graph.nodes.retriever import retriever_node, retriever_quick_node
from graph.nodes.reasoning import reasoning_node
from graph.nodes.review_analyzer import review_analyzer_node
from graph.nodes.synthesis import synthesis_node, synthesis_quick_node
from graph.nodes.cost_tracker import cost_tracker_node
from graph.nodes.confidence import confidence_node
from graph.nodes.web_search import web_search_node
from graph.nodes.web_scraper import web_scraper_node
from graph.nodes.auto_indexer import auto_indexer_node


def build_graph() -> StateGraph:
    """Build and return the compiled research graph."""

    builder = StateGraph(ResearchState)

    # ── Register all nodes ────────────────────────────────────────
    builder.add_node("mode_router", mode_router_node)
    builder.add_node("clarification", clarification_node)
    builder.add_node("planner", planner_node)
    builder.add_node("retriever", retriever_node)
    builder.add_node("retriever_quick", retriever_quick_node)
    builder.add_node("reasoning", reasoning_node)
    builder.add_node("review_analyzer", review_analyzer_node)
    builder.add_node("synthesis", synthesis_node)
    builder.add_node("synthesis_quick", synthesis_quick_node)
    builder.add_node("cost_tracker", cost_tracker_node)
    builder.add_node("confidence", confidence_node)

    # New autonomous research nodes
    builder.add_node("web_search", web_search_node)
    builder.add_node("web_search_quick", web_search_node)   # same function, different graph node name
    builder.add_node("web_scraper", web_scraper_node)
    builder.add_node("web_scraper_quick", web_scraper_node)
    builder.add_node("auto_indexer", auto_indexer_node)
    builder.add_node("auto_indexer_quick", auto_indexer_node)

    # ── Entry point ───────────────────────────────────────────────
    builder.set_entry_point("mode_router")

    # ── Mode routing: Quick vs Deep ───────────────────────────────
    builder.add_conditional_edges(
        "mode_router",
        route_by_mode,
        {
            "retriever_quick": "web_search_quick",   # Quick path now starts with web search
            "clarification": "clarification",
        },
    )

    # ── Deep path ─────────────────────────────────────────────────
    builder.add_conditional_edges(
        "clarification",
        route_after_clarification,
        {
            "needs_clarification": END,   # API returns the clarification question
            "planner": "planner",
        },
    )
    # Planner → web search → scrape → auto-index → retriever
    builder.add_edge("planner", "web_search")
    builder.add_edge("web_search", "web_scraper")
    builder.add_edge("web_scraper", "auto_indexer")
    builder.add_edge("auto_indexer", "retriever")

    # Parallelize reasoning and review analysis
    builder.add_edge("retriever", "reasoning")
    builder.add_edge("retriever", "review_analyzer")
    
    # Join back at synthesis
    builder.add_edge("reasoning", "synthesis")
    builder.add_edge("review_analyzer", "synthesis")
    builder.add_edge("synthesis", "cost_tracker")

    # ── Quick path ────────────────────────────────────────────────
    # web_search_quick → scrape → auto-index → retriever_quick → synthesis_quick
    builder.add_edge("web_search_quick", "web_scraper_quick")
    builder.add_edge("web_scraper_quick", "auto_indexer_quick")
    builder.add_edge("auto_indexer_quick", "retriever_quick")
    builder.add_edge("retriever_quick", "synthesis_quick")
    builder.add_edge("synthesis_quick", "cost_tracker")

    # ── Shared final nodes ────────────────────────────────────────
    builder.add_edge("cost_tracker", "confidence")
    builder.add_edge("confidence", END)

    return builder.compile()


# Singleton compiled graph
_graph = None


def get_graph():
    global _graph
    if _graph is None:
        _graph = build_graph()
    return _graph

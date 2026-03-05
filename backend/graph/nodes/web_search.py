"""
graph/nodes/web_search.py – Web search using DuckDuckGo (free, no API key).
Fetches fresh external data to feed into the scraper and auto-indexer.
"""

import logging
from graph.state import ResearchState
from config import settings

logger = logging.getLogger(__name__)


def _search_ddg(query: str, max_results: int = 5) -> list[dict]:
    """Run a DuckDuckGo text search and return [{title, url, snippet}]."""
    try:
        from ddgs import DDGS
        with DDGS() as ddgs:
            results = []
            for r in ddgs.text(query, max_results=max_results):
                results.append({
                    "title": r.get("title", ""),
                    "url": r.get("href", ""),
                    "snippet": r.get("body", ""),
                })
            return results
    except Exception as e:
        logger.warning(f"DuckDuckGo search failed for '{query}': {e}")
        return []


def web_search_node(state: ResearchState) -> ResearchState:
    """
    Search the web for the user's query.
    In deep mode, searches each sub-question for broader coverage.
    Skipped entirely if WEB_SEARCH_ENABLED is False.
    """
    if not settings.WEB_SEARCH_ENABLED:
        state["search_results"] = []
        state["web_sources"] = []
        return state

    max_results = settings.WEB_SEARCH_MAX_RESULTS

    # Determine what to search
    queries = state.get("sub_questions", [])
    if not queries:
        queries = [state["query"]]

    all_results: list[dict] = []
    seen_urls: set[str] = set()

    for q in queries:
        hits = _search_ddg(q, max_results=max_results)
        for hit in hits:
            url = hit.get("url", "")
            if url and url not in seen_urls:
                seen_urls.add(url)
                all_results.append(hit)

    # Cap total results
    all_results = all_results[:max_results * 2]

    state["search_results"] = all_results
    state["web_sources"] = [r["url"] for r in all_results if r.get("url")]

    logger.info(f"Web search returned {len(all_results)} results for {len(queries)} queries")
    return state

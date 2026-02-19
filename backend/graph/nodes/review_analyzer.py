"""
graph/nodes/review_analyzer.py – dedicated node for structured review analysis.
"""

from langchain_core.messages import SystemMessage, HumanMessage
from graph.state import ResearchState
from llm.provider import get_llm

REVIEW_ANALYZER_SYSTEM = """You are an expert e-commerce data analyst.
Your job is to analyze raw customer reviews and extract structured complaint themes.

Rules:
- Identify the top 3-5 recurring complaint themes.
- For each theme, estimate the sentiment severity (Critical, Major, Minor).
- Count the approximate mentions (e.g., "15 mentions").
- Output a structured Markdown summary.
- If no reviews are found, output "No reviews available for analysis."
"""

REVIEW_ANALYZER_HUMAN = """Reviews to analyze:
{reviews}

Extract top complaint themes in this format:
- **Theme Name** (Severity): Count - "Representative quote"
"""

def review_analyzer_node(state: ResearchState) -> ResearchState:
    """
    Analyzes specific review chunks to extract structured complaint data.
    Runs in parallel with reasoning/planning.
    """
    llm = get_llm(temperature=0.1)
    
    # Filter for chunks that are explicitly reviews
    # (Metadata type='reviews' is set by /products/analyze endpoint)
    review_chunks = [
        c.get("text", "") 
        for c in state.get("retrieved_chunks", []) 
        if c.get("metadata", {}).get("type") == "reviews"
    ]
    
    # If no specific review metadata, try to guess from source or content
    if not review_chunks:
        review_chunks = [
            c.get("text", "") 
            for c in state.get("retrieved_chunks", []) 
            if "review" in c.get("source", "").lower() or "review" in c.get("text", "")[:50].lower()
        ]

    if not review_chunks:
        return {"review_analysis": "No structured reviews found in context."}

    # Combine reviews (truncate if too long)
    combined_reviews = "\n\n".join(review_chunks)[:20000]

    try:
        response = llm.invoke([
            SystemMessage(content=REVIEW_ANALYZER_SYSTEM),
            HumanMessage(content=REVIEW_ANALYZER_HUMAN.format(reviews=combined_reviews)),
        ])
        return {"review_analysis": response.content.strip()}
    except Exception as e:
        return {"review_analysis": f"Error interpreting reviews: {str(e)}"}


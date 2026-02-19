"""
main.py – FastAPI application for Researcho.

Endpoints:
  GET  /health                  – liveness check
  GET  /                        – serves frontend index.html
  POST /research                – run a research query
  GET  /preferences/{user_id}  – get user preferences
  PUT  /preferences/{user_id}  – update user preferences
  POST /documents/index        – index a document chunk
"""

import time
from pathlib import Path
from typing import Optional, Literal

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel

from config import settings
from graph.orchestrator import get_graph
from memory.preference_memory import load_preferences, save_preferences
from memory.history_memory import save_research
from memory.document_memory import index_document

# ── App setup ─────────────────────────────────────────────────────────────────
app = FastAPI(
    title="Researcho – E-Commerce Intelligence API",
    description="AI business analyst for product managers. Analyzes reviews, pricing, competitors, and margin impact.",
    version="2.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS.split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Static frontend ───────────────────────────────────────────────────────────
# CSS/JS served at /static/style.css and /static/app.js
# index.html served directly at / via the route below
FRONTEND_PATH = Path(__file__).parent.parent / "frontend"
if FRONTEND_PATH.exists():
    app.mount("/static", StaticFiles(directory=str(FRONTEND_PATH)), name="static")


# ── Request / Response models ─────────────────────────────────────────────────

class ResearchRequest(BaseModel):
    query: str
    mode: Literal["quick", "deep"] = "quick"
    user_id: str = "anonymous"
    clarification_answer: Optional[str] = None


class ResearchResponse(BaseModel):
    query: str
    mode: str
    report: Optional[str] = None
    needs_clarification: bool = False
    clarification_question: Optional[str] = None
    confidence: float = 0.0
    input_tokens: int = 0
    output_tokens: int = 0
    estimated_cost: float = 0.0
    latency: float = 0.0
    error: Optional[str] = None


class PreferencesModel(BaseModel):
    prefers_code_examples: bool = False
    expertise_level: Literal["beginner", "intermediate", "advanced"] = "intermediate"
    preferred_answer_length: Literal["short", "detailed"] = "detailed"
    # E-Commerce domain preferences
    focus_area: Literal["margins", "reviews", "pricing", "competitor_gap", "general"] = "general"
    business_role: Literal["product_manager", "analyst", "founder", "general"] = "general"
    primary_metric: Literal["revenue", "conversion", "return_rate", "margin", "general"] = "general"


class DocumentIndexRequest(BaseModel):
    text: str
    source: str
    metadata: Optional[dict] = None


class ProductAnalyzeRequest(BaseModel):
    """Submit structured product data for analysis. Auto-indexes into memory then runs research."""
    product_name: str
    query: str = "Why is this product underperforming?"
    mode: Literal["quick", "deep"] = "deep"
    user_id: str = "anonymous"
    reviews: Optional[list] = None              # list of review strings
    price: Optional[float] = None               # your product price
    competitor_prices: Optional[dict] = None    # {competitor_name: price}
    sales_data: Optional[dict] = None           # {metric: value} e.g. {"conversion": 0.02}


# ── Routes ────────────────────────────────────────────────────────────────────

@app.get("/health")
async def health():
    return {"status": "ok", "version": "1.0.0"}


@app.get("/")
async def root():
    """Serve the frontend UI."""
    if FRONTEND_PATH.exists():
        return FileResponse(str(FRONTEND_PATH / "index.html"), media_type="text/html; charset=utf-8")
    return {"message": "Researcho API running. Visit /docs for API docs."}


@app.post("/research", response_model=ResearchResponse)
async def research(request: ResearchRequest):
    """
    Run a research query.
    - mode=quick : fast single-pass answer (<30s)
    - mode=deep  : plan → retrieve → reason → synthesize (<3min)

    If deep mode returns needs_clarification=True, re-submit with clarification_answer.
    """
    prefs = load_preferences(request.user_id)

    initial_state = {
        "query": request.query.strip(),
        "mode": request.mode,
        "user_id": request.user_id,
        "clarification_answer": request.clarification_answer,
        **prefs,
    }

    graph = get_graph()
    start = time.time()

    try:
        final_state = graph.invoke(initial_state)
    except Exception as e:
        return ResearchResponse(
            query=request.query,
            mode=request.mode,
            error=f"Graph execution error: {str(e)}",
        )

    latency = round(time.time() - start, 2)
    final_state["latency"] = latency

    # Persist completed research to memory
    if final_state.get("report") and not final_state.get("needs_clarification"):
        try:
            save_research(
                user_id=request.user_id,
                query=request.query,
                mode=request.mode,
                summary=final_state["report"][:500],
                key_findings=final_state.get("reasoning_notes", "")[:500],
            )
        except Exception:
            pass

    return ResearchResponse(
        query=request.query,
        mode=request.mode,
        report=final_state.get("report"),
        needs_clarification=final_state.get("needs_clarification", False),
        clarification_question=final_state.get("clarification_question"),
        confidence=final_state.get("confidence", 0.0),
        input_tokens=final_state.get("input_tokens", 0),
        output_tokens=final_state.get("output_tokens", 0),
        estimated_cost=final_state.get("estimated_cost", 0.0),
        latency=latency,
        error=final_state.get("error"),
    )


@app.get("/preferences/{user_id}", response_model=PreferencesModel)
async def get_preferences(user_id: str):
    prefs = load_preferences(user_id)
    return PreferencesModel(**prefs)


@app.put("/preferences/{user_id}")
async def update_preferences(user_id: str, prefs: PreferencesModel):
    save_preferences(user_id, prefs.model_dump())
    return {"status": "saved", "user_id": user_id}


@app.post("/documents/index")
async def index_doc(request: DocumentIndexRequest):
    """Index a document chunk for future retrieval."""
    try:
        index_document(
            text=request.text,
            source=request.source,
            metadata=request.metadata,
        )
        return {"status": "indexed", "source": request.source}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/products/analyze", response_model=ResearchResponse)
async def analyze_product(request: ProductAnalyzeRequest):
    """
    E-Commerce Intelligence endpoint.
    Submit product data (reviews, pricing, competitor info) and get a decision-ready business report.
    Data is auto-indexed into memory for future retrieval.
    """
    # ── Auto-index all submitted data into document memory ──────────────────
    source = f"product:{request.product_name}"
    chunks_indexed = 0

    if request.reviews:
        review_text = "\n".join(
            [f"Review {i+1}: {r}" for i, r in enumerate(request.reviews)]
        )
        try:
            index_document(
                text=f"Customer reviews for {request.product_name}:\n{review_text}",
                source=source,
                metadata={"type": "reviews", "product": request.product_name},
            )
            chunks_indexed += 1
        except Exception:
            pass

    if request.price is not None or request.competitor_prices:
        pricing_parts = [f"{request.product_name} price: ${request.price}" if request.price else ""]
        if request.competitor_prices:
            for comp, price in request.competitor_prices.items():
                pricing_parts.append(f"{comp} price: ${price}")
        try:
            index_document(
                text="Pricing data:\n" + "\n".join(filter(None, pricing_parts)),
                source=source,
                metadata={"type": "pricing", "product": request.product_name},
            )
            chunks_indexed += 1
        except Exception:
            pass

    if request.sales_data:
        sales_text = "\n".join([f"{k}: {v}" for k, v in request.sales_data.items()])
        try:
            index_document(
                text=f"Sales & performance metrics for {request.product_name}:\n{sales_text}",
                source=source,
                metadata={"type": "sales", "product": request.product_name},
            )
            chunks_indexed += 1
        except Exception:
            pass

    # ── Enrich query with product context ──────────────────────────────────
    enriched_query = f"Product: {request.product_name}\n\nQuery: {request.query}"

    # ── Run through research graph ──────────────────────────────────────────
    prefs = load_preferences(request.user_id)
    initial_state = {
        "query": enriched_query,
        "mode": request.mode,
        "user_id": request.user_id,
        **prefs,
    }

    graph = get_graph()
    start = time.time()
    try:
        final_state = graph.invoke(initial_state)
    except Exception as e:
        return ResearchResponse(
            query=enriched_query,
            mode=request.mode,
            error=f"Analysis error: {str(e)}",
        )

    latency = round(time.time() - start, 2)
    final_state["latency"] = latency

    if final_state.get("report") and not final_state.get("needs_clarification"):
        try:
            save_research(
                user_id=request.user_id,
                query=enriched_query,
                mode=request.mode,
                summary=final_state["report"][:500],
                key_findings=final_state.get("reasoning_notes", "")[:500],
            )
        except Exception:
            pass

    return ResearchResponse(
        query=enriched_query,
        mode=request.mode,
        report=final_state.get("report"),
        needs_clarification=final_state.get("needs_clarification", False),
        clarification_question=final_state.get("clarification_question"),
        confidence=final_state.get("confidence", 0.0),
        input_tokens=final_state.get("input_tokens", 0),
        output_tokens=final_state.get("output_tokens", 0),
        estimated_cost=final_state.get("estimated_cost", 0.0),
        latency=latency,
        error=final_state.get("error"),
    )


# ── Entrypoint ────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.APP_HOST,
        port=settings.APP_PORT,
        reload=True,
        # Exclude venv from file watcher — prevents constant restarts
        reload_excludes=["**/venv/**", "**/*.pyc", "**/__pycache__/**"],
    )

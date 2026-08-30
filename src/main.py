"""FastAPI application entrypoint for the HorRAGor Part 3 Multi-Agent architecture.

Exposes:
- GET  /health : System status and active architecture.
- POST /chat   : Asynchronous multi-agent execution pipeline.
"""

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from backend.data.faiss_index import TitleIndex
from backend.tools.faiss_tool import set_index
from src.config import settings
from src.graph.pipeline import run_agent_pipeline

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("horragor-api")


# --- Lifespan Context: In-Memory FAISS Index Loading ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Loads the FAISS index into RAM once during server startup for zero-latency lookups."""
    if TitleIndex.exists():
        index = TitleIndex.load()
        set_index(index)
        logger.info("FAISS Title Index successfully loaded into RAM (%d horror titles).", len(index))
    else:
        logger.warning(
            "FAISS index not found at %s. validate_film will operate in degraded mode.",
            settings.resolved_faiss_dir,
        )
    yield


app = FastAPI(
    title="HorRAGor3 — Multi-Agent Horror Assistant API",
    version="0.3.0",
    lifespan=lifespan,
)

# Enable CORS for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- Request & Response Schemas ---
class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, description="User question or prompt about a horror film")


class ChatResponse(BaseModel):
    answer: str
    sources: list[str] = Field(default_factory=list)
    extracted_title: str | None = None
    context_summary: str | None = None
    architecture: str = "LangGraph Multi-Agent"


# --- API Routes ---
@app.get("/health")
def health() -> dict[str, str]:
    """Healthcheck endpoint."""
    return {
        "status": "ok",
        "app": "HorRAGor3",
        "architecture": "LangGraph Multi-Agent (RAG + Scraper + Gothic Writer)",
    }


@app.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest) -> ChatResponse:
    """Executes the distributed multi-agent pipeline for the user message."""
    try:
        result = await run_agent_pipeline(req.message)
        return ChatResponse(
            answer=result["answer"],
            sources=result.get("sources", []),
            extracted_title=result.get("extracted_title"),
            context_summary=result.get("context_summary"),
        )
    except Exception as exc:
        logger.exception("Error executing multi-agent pipeline: %s", exc)
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred in the multi-agent pipeline: {exc}",
        ) from exc


def run() -> None:
    """CLI runner function for uvicorn."""
    import uvicorn
    uvicorn.run(
        "src.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=True,
    )


if __name__ == "__main__":
    run()

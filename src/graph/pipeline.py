"""LangGraph Multi-Agent StateGraph pipeline assembly and execution engine.

Coordinates:
START -> rag_node -> [route_after_rag] -> (scraper_node -> narration_node | narration_node) -> END
"""

import asyncio
import logging
from typing import Any
from langgraph.graph import END, START, StateGraph

from src.config import settings
from src.graph.nodes import narration_node, rag_node, scraper_node
from src.graph.router import route_after_rag
from src.models.state import HorragorState

logger = logging.getLogger(__name__)


def get_callbacks() -> list[Any]:
    """Instantiates Langfuse CallbackHandler if enabled in settings."""
    callbacks = []
    if settings.langfuse_enabled:
        try:
            import os

            if settings.langfuse_public_key:
                os.environ["LANGFUSE_PUBLIC_KEY"] = settings.langfuse_public_key
            if settings.langfuse_secret_key:
                os.environ["LANGFUSE_SECRET_KEY"] = settings.langfuse_secret_key
            if settings.langfuse_host:
                os.environ["LANGFUSE_HOST"] = settings.langfuse_host

            try:
                from langfuse.langchain import CallbackHandler
            except ImportError:
                from langfuse.callback import CallbackHandler

            try:
                handler = CallbackHandler(public_key=settings.langfuse_public_key)
            except TypeError:
                handler = CallbackHandler()

            callbacks.append(handler)
            logger.info("Langfuse CallbackHandler successfully attached to multi-agent pipeline.")
        except Exception as exc:
            logger.warning(f"Failed to initialize Langfuse CallbackHandler: {exc}")
    return callbacks


def build_pipeline():
    """Builds and compiles the HorRAGor multi-agent StateGraph."""
    graph = StateGraph(HorragorState)

    # 1. Register specialized nodes
    graph.add_node("rag_node", rag_node)
    graph.add_node("scraper_node", scraper_node)
    graph.add_node("narration_node", narration_node)

    # 2. Add edges & conditional branching
    graph.add_edge(START, "rag_node")
    graph.add_conditional_edges(
        "rag_node",
        route_after_rag,
        {
            "scraper_node": "scraper_node",
            "narration_node": "narration_node",
        },
    )
    graph.add_edge("scraper_node", "narration_node")
    graph.add_edge("narration_node", END)

    return graph.compile()


# Singleton compiled graph instance
_compiled_pipeline = None


def get_pipeline():
    """Returns the cached compiled StateGraph pipeline."""
    global _compiled_pipeline
    if _compiled_pipeline is None:
        _compiled_pipeline = build_pipeline()
    return _compiled_pipeline


async def run_agent_pipeline(
    query: str,
    history: list[dict[str, Any]] | None = None,
    active_title: str | None = None,
) -> dict[str, Any]:
    """Asynchronously executes the HorRAGor multi-agent pipeline for a given query."""
    pipeline = get_pipeline()
    initial_state: HorragorState = {
        "query": query,
        "sources": [],
        "conversation_history": history or [],
        "active_title": active_title,
    }

    callbacks = get_callbacks()
    config = {"callbacks": callbacks} if callbacks else None

    # Run in a thread to keep FastAPI async event loop unblocked
    if config:
        final_state = await asyncio.to_thread(pipeline.invoke, initial_state, config=config)
    else:
        final_state = await asyncio.to_thread(pipeline.invoke, initial_state)

    return {
        "answer": final_state.get("final_narrative") or "Aucune réponse générée.",
        "sources": final_state.get("sources", []),
        "extracted_title": final_state.get("extracted_title"),
        "active_title": final_state.get("active_title") or final_state.get("extracted_title"),
        "context_summary": final_state.get("context_summary"),
        "state": final_state,
    }

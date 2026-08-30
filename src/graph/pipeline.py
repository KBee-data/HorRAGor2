"""LangGraph Multi-Agent StateGraph pipeline assembly and execution engine.

Coordinates:
START -> rag_node -> [route_after_rag] -> (scraper_node -> narration_node | narration_node) -> END
"""

import asyncio
from typing import Any
from langgraph.graph import END, START, StateGraph

from src.graph.nodes import narration_node, rag_node, scraper_node
from src.graph.router import route_after_rag
from src.models.state import HorragorState


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

    # Run in a thread to keep FastAPI async event loop unblocked
    final_state = await asyncio.to_thread(pipeline.invoke, initial_state)
    return {
        "answer": final_state.get("final_narrative") or "Aucune réponse générée.",
        "sources": final_state.get("sources", []),
        "extracted_title": final_state.get("extracted_title"),
        "active_title": final_state.get("active_title") or final_state.get("extracted_title"),
        "context_summary": final_state.get("context_summary"),
        "state": final_state,
    }

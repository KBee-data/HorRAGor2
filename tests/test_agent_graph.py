"""Tests du durcissement d'AgentGraph (sans LLM : graphe factice)."""

import pytest
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
from langgraph.errors import GraphRecursionError

from backend.agent.graph import AgentGraph, _as_text, _build_trace
from backend.contracts.schemas import ChatRequest


def test_as_text_normalises_content():
    assert _as_text("hello") == "hello"
    assert _as_text(None) == ""
    assert _as_text([{"text": "a"}, {"text": "b"}]) == "a b"


def _engine_with_graph(graph) -> AgentGraph:
    # __new__ : on evite __init__ (qui compilerait le vrai graphe / chargerait le LLM).
    engine = AgentGraph.__new__(AgentGraph)
    engine._graph = graph
    return engine


@pytest.mark.asyncio
async def test_run_handles_recursion_error():
    class _Loop:
        def invoke(self, *a, **k):
            raise GraphRecursionError("boucle")

    resp = await _engine_with_graph(_Loop()).run(ChatRequest(message="x"))
    assert resp.verdict == "error"
    assert resp.answer  # message poli, pas d'exception


@pytest.mark.asyncio
async def test_run_handles_unexpected_error():
    class _Boom:
        def invoke(self, *a, **k):
            raise RuntimeError("oops")

    resp = await _engine_with_graph(_Boom()).run(ChatRequest(message="x"))
    assert resp.verdict == "error"
    assert resp.answer


def test_build_trace_captures_tools_and_verdict():
    ai = AIMessage(
        content="", tool_calls=[{"name": "lookup_movie", "args": {"title": "X"}, "id": "a"}]
    )
    tool = ToolMessage(content="{'title': 'X'}", tool_call_id="a")
    final = AIMessage(content="réponse")
    state = {"messages": [HumanMessage("q"), ai, tool, final], "verdict": "valid"}

    steps = _build_trace(state)

    assert steps[0].kind == "tool" and steps[0].name == "lookup_movie"
    assert "X" in steps[0].detail
    assert steps[-1].kind == "verdict" and steps[-1].name == "valid"

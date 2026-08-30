"""Unit and integration tests for the HorRAGor Part 3 Multi-Agent Architecture."""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch

from src.graph.nodes import _build_context_summary
from src.graph.pipeline import build_pipeline
from src.graph.router import route_after_rag
from src.main import app
from src.models.state import HorragorState


def test_router_conditional_branching():
    """Verify conditional router directs to narration if local data is complete, else to scraper."""
    state_sufficient: HorragorState = {
        "query": "The Thing",
        "is_local_info_sufficient": True,
    }
    assert route_after_rag(state_sufficient) == "narration_node"

    state_incomplete: HorragorState = {
        "query": "Unknown Movie 1999",
        "is_local_info_sufficient": False,
    }
    assert route_after_rag(state_incomplete) == "scraper_node"


def test_context_summary_building():
    """Verify context trimming isolates facts cleanly without technical schema pollution."""
    state: HorragorState = {
        "query": "Who directed The Thing?",
        "rag_data": {
            "found": True,
            "matched_title": "The Thing",
            "director": "John Carpenter",
            "release_year": 1982,
            "genres": ["Horror", "Sci-Fi"],
            "vote_average": 8.2,
            "cast": ["Kurt Russell", "Wilford Brimley"],
            "synopsis": "Scientists in Antarctica encounter a shape-shifting alien.",
            "similar_movies": ["Alien", "The Fly"],
        },
        "web_data": "Additional trivia: Released in 1982 to critical acclaim later on.",
    }

    summary = _build_context_summary(state)
    assert "The Thing" in summary
    assert "John Carpenter" in summary
    assert "1982" in summary
    assert "Kurt Russell" in summary
    assert "Additional trivia" in summary


def test_pipeline_graph_structure():
    """Verify that the StateGraph compiles cleanly with all required nodes and edges."""
    pipeline = build_pipeline()
    assert pipeline is not None
    nodes = list(pipeline.nodes.keys())
    assert "rag_node" in nodes
    assert "scraper_node" in nodes
    assert "narration_node" in nodes


def test_fastapi_health_endpoint():
    """Verify GET /health returns 200 and indicates HorRAGor3 architecture."""
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["app"] == "HorRAGor3"


@pytest.mark.asyncio
async def test_fastapi_chat_endpoint_mocked():
    """Verify POST /chat executes successfully and returns expected payload structure."""
    client = TestClient(app)
    mock_result = {
        "answer": "In the desolate frozen wastes of Antarctica, John Carpenter summons an ancient terror...",
        "sources": ["FAISS Vector Index", "Local Horror DB"],
        "extracted_title": "The Thing",
        "context_summary": "Title: The Thing | Director: John Carpenter",
        "state": {},
    }

    with patch("src.main.run_agent_pipeline", new_callable=AsyncMock) as mock_pipeline:
        mock_pipeline.return_value = mock_result
        response = client.post("/chat", json={"message": "Who directed The Thing?"})
        assert response.status_code == 200
        payload = response.json()
        assert "John Carpenter" in payload["answer"]
        assert "FAISS Vector Index" in payload["sources"]
        assert payload["extracted_title"] == "The Thing"

"""Unit and integration tests for the HorRAGor Part 3 Multi-Agent Architecture."""

import uuid
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


def test_anaphoric_title_resolution():
    """Verify that follow-up questions with pronouns resolve to active_title."""
    from src.tools.rag_tool import _extract_candidate_title

    # Direct title extraction
    assert _extract_candidate_title("Who directed The Thing?") == "The Thing"

    # Follow-up with pronoun resolving to active_title
    assert _extract_candidate_title("What year was it released?", active_title="The Thing") == "The Thing"
    assert _extract_candidate_title("Quand est-il sorti ?", active_title="Alien") == "Alien"
    assert _extract_candidate_title("Who acted in this movie?", active_title="Hereditary") == "Hereditary"

    # New film mentioned overrides active_title
    assert _extract_candidate_title("Tell me about Halloween", active_title="The Thing") == "Halloween"


def test_auth_registration_and_login():
    """Verify user registration, login, and token generation."""
    client = TestClient(app)
    unique_username = f"testuser_{uuid.uuid4().hex[:6]}"
    reg_payload = {
        "username": unique_username,
        "email": f"{unique_username}@horragor.ai",
        "password": "strongpassword123",
    }
    # 1. Register
    reg_resp = client.post("/auth/register", json=reg_payload)
    assert reg_resp.status_code == 201
    assert reg_resp.json()["username"] == unique_username

    # 2. Login (OAuth2 form-data)
    login_resp = client.post(
        "/auth/login",
        data={"username": unique_username, "password": "strongpassword123"},
    )
    assert login_resp.status_code == 200
    token_data = login_resp.json()
    assert "access_token" in token_data
    assert "refresh_token" in token_data
    assert token_data["token_type"] == "bearer"


def test_unauthorized_chat_blocked():
    """Verify POST /chat returns 401 Unauthorized when no Bearer token is provided."""
    client = TestClient(app)
    response = client.post("/chat", json={"message": "Who directed The Thing?"})
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_fastapi_chat_endpoint_mocked():
    """Verify POST /chat executes successfully when authorized with a Bearer token."""
    from src.auth.security import create_access_token

    client = TestClient(app)
    mock_result = {
        "answer": "The Thing was released into our world in 1982 by John Carpenter...",
        "sources": ["FAISS Vector Index", "Wikipedia Web Scraper"],
        "extracted_title": "The Thing",
        "active_title": "The Thing",
        "context_summary": "Title: The Thing | Director: John Carpenter",
        "state": {},
    }

    # Generate a valid test access token
    test_token = create_access_token(data={"sub": "admin", "email": "admin@horragor.ai"})

    # Ensure admin user exists in DB
    from src.auth.service import get_user_by_username, register_user
    from src.auth.models import UserCreate

    if not get_user_by_username("admin"):
        try:
            register_user(UserCreate(username="admin", email="admin@horragor.ai", password="adminpassword123"))
        except Exception:
            pass

    with patch("src.main.run_agent_pipeline", new_callable=AsyncMock) as mock_pipeline:
        mock_pipeline.return_value = mock_result
        response = client.post(
            "/chat",
            headers={"Authorization": f"Bearer {test_token}"},
            json={
                "message": "What year was it released?",
                "history": [{"role": "user", "content": "Who directed The Thing?"}],
                "active_title": "The Thing",
            },
        )
        assert response.status_code == 200
        payload = response.json()
        assert "1982" in payload["answer"]
        assert payload["active_title"] == "The Thing"


def test_langfuse_settings_validation():
    """Verify enterprise validation guard: keys required if langfuse_enabled=True."""
    from pydantic import ValidationError
    from src.config import Settings

    # 1. Disabled: succeeds with default None keys
    s_disabled = Settings(langfuse_enabled=False)
    assert s_disabled.langfuse_enabled is False

    # 2. Enabled with valid keys: succeeds
    s_enabled = Settings(
        langfuse_enabled=True,
        langfuse_public_key="pk-lf-test-key",
        langfuse_secret_key="sk-lf-test-key",
        langfuse_host="http://localhost:3000",
    )
    assert s_enabled.langfuse_enabled is True
    assert s_enabled.langfuse_public_key == "pk-lf-test-key"

    # 3. Enabled with missing keys: raises ValidationError (Enterprise Security Guard)
    with pytest.raises(ValidationError):
        Settings(langfuse_enabled=True, langfuse_public_key=None, langfuse_secret_key=None)


def test_langfuse_callback_instantiation():
    """Verify get_callbacks returns empty list when disabled and instantiates CallbackHandler when enabled."""
    from src.graph.pipeline import get_callbacks

    # When disabled
    with patch("src.graph.pipeline.settings.langfuse_enabled", False):
        assert get_callbacks() == []

    # When enabled with valid keys
    with patch("src.graph.pipeline.settings.langfuse_enabled", True), \
         patch("src.graph.pipeline.settings.langfuse_public_key", "pk-lf-test"), \
         patch("src.graph.pipeline.settings.langfuse_secret_key", "sk-lf-test"), \
         patch("src.graph.pipeline.settings.langfuse_host", "http://localhost:3000"):
        callbacks = get_callbacks()
        assert len(callbacks) == 1
        assert callbacks[0].__class__.__name__ in ("CallbackHandler", "LangchainCallbackHandler")


def test_director_mismatch_triggers_scraper():
    """Verify that when the query specifies a director contradictory to local DB, is_sufficient is False."""
    from src.graph.nodes import rag_node

    state = {
        "query": "What about the comedy Scary Movie directed by Keenan Ivory Wayans?",
        "sources": [],
    }
    result = rag_node(state)
    assert result["is_local_info_sufficient"] is False
    assert result["extracted_title"] == "Scary Movie"


def test_conversational_question_entity_extraction():
    """Verify that complex conversational phrasing correctly extracts clean title and constraints."""
    from src.tools.rag_tool import extract_query_constraints

    title, director, year = extract_query_constraints(
        "What can you tell me about the comedy Scary Movie directed by Keenan Ivory Wayans?"
    )
    assert title == "Scary Movie"
    assert "Keenan" in (director or "") or "Keenen" in (director or "")





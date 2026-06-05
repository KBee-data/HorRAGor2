"""Test d'integration de l'API via httpx + transport ASGI.

Le moteur reel (AgentGraph) necessite Ollama + la base : on le SURCHARGE par le
FakeEngine pour des tests rapides, deterministes et hors-ligne.
"""

import httpx
import pytest

from backend.api.deps import get_engine
from backend.api.main import app
from backend.mocks.fake_engine import FakeEngine

app.dependency_overrides[get_engine] = lambda: FakeEngine()


@pytest.mark.asyncio
async def test_health():
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


@pytest.mark.asyncio
async def test_chat_returns_fixture_answer():
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post("/chat", json={"message": "Qui a realise The Thing ?"})
    assert resp.status_code == 200
    body = resp.json()
    assert "answer" in body and body["answer"]
    assert body["sources"] == ["mock:fixtures"]

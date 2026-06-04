"""Test d'integration de l'API (mockee) via httpx + transport ASGI."""

import httpx
import pytest

from backend.api.main import app


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

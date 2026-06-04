"""Tests des contrats partages + du mock (servent d'exemple a toute l'equipe)."""

import pytest

from backend.contracts.schemas import ChatRequest, ChatResponse
from backend.mocks.fake_engine import FakeEngine


def test_chat_schemas_roundtrip():
    req = ChatRequest(message="Qui a realise The Thing ?")
    assert req.session_id == "default"
    resp = ChatResponse(answer="John Carpenter", sources=["sql"])
    assert resp.model_dump()["answer"] == "John Carpenter"


@pytest.mark.asyncio
async def test_fake_engine_respects_contract():
    engine = FakeEngine()
    resp = await engine.run(ChatRequest(message="test"))
    assert isinstance(resp, ChatResponse)
    assert resp.answer
    assert resp.sources == ["mock:fixtures"]

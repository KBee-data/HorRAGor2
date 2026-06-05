"""Tests du helper d'embedding — l'appel Ollama est MOQUE (CI sans modele)."""

import httpx
import pytest

from backend.config import settings
from backend.data import embed


class _FakeResponse:
    def __init__(self, payload: dict, status_code: int = 200):
        self._payload = payload
        self.status_code = status_code
        self.text = str(payload)

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise httpx.HTTPStatusError("err", request=None, response=None)

    def json(self) -> dict:
        return self._payload


def test_embed_texts_batch(monkeypatch):
    # Ollama renvoie un vecteur de la bonne dimension par texte.
    fake = [[0.0] * settings.embedding_dim, [1.0] * settings.embedding_dim]
    monkeypatch.setattr(httpx, "post", lambda *a, **k: _FakeResponse({"embeddings": fake}))

    out = embed.embed_texts(["The Thing", "Hereditary"])
    assert len(out) == 2
    assert len(out[0]) == settings.embedding_dim


def test_embed_texts_empty_shortcircuits(monkeypatch):
    # Liste vide : aucun appel reseau ne doit etre fait.
    def _boom(*a, **k):  # pragma: no cover
        raise AssertionError("httpx.post ne devrait pas etre appele")

    monkeypatch.setattr(httpx, "post", _boom)
    assert embed.embed_texts([]) == []


def test_embed_texts_dimension_mismatch_raises(monkeypatch):
    wrong = [[0.0] * (settings.embedding_dim + 1)]
    monkeypatch.setattr(httpx, "post", lambda *a, **k: _FakeResponse({"embeddings": wrong}))
    with pytest.raises(ValueError):
        embed.embed_texts(["x"])

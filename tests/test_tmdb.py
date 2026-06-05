"""Test du client TMDB — appel HTTP MOQUE (pas de reseau)."""

import httpx

from backend.data import tmdb


class _FakeResponse:
    def __init__(self, payload):
        self._payload = payload

    def raise_for_status(self):
        pass

    def json(self):
        return self._payload


def test_get_credits_parses_director_and_cast(monkeypatch):
    payload = {
        "crew": [
            {"job": "Editor", "name": "X"},
            {"job": "Director", "name": "Ari Aster"},
        ],
        "cast": [
            {"name": "Toni Collette"},
            {"name": "Alex Wolff"},
            {"name": "Milly Shapiro"},
        ],
    }
    monkeypatch.setattr(httpx, "get", lambda *a, **k: _FakeResponse(payload))

    out = tmdb.get_credits(493, top_cast=2)
    assert out["director"] == "Ari Aster"
    assert out["cast"] == ["Toni Collette", "Alex Wolff"]  # tronque a top_cast

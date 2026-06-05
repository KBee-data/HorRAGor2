"""Test du tool Wikipedia — appel HTTP MOQUE."""

import httpx

from backend.tools import wikipedia_tool


class _Resp:
    def __init__(self, status_code: int, payload: dict):
        self.status_code = status_code
        self._payload = payload

    def json(self) -> dict:
        return self._payload


def test_scrape_returns_extract(monkeypatch):
    payload = {"type": "standard", "extract": "A 1982 horror film."}
    monkeypatch.setattr(httpx, "get", lambda *a, **k: _Resp(200, payload))
    out = wikipedia_tool.scrape_detailed_synopsis("The Thing")
    assert out is not None and "1982" in out


def test_scrape_disambiguation_returns_none(monkeypatch):
    monkeypatch.setattr(httpx, "get", lambda *a, **k: _Resp(200, {"type": "disambiguation"}))
    assert wikipedia_tool.scrape_detailed_synopsis("Alien") is None


def test_scrape_404_returns_none(monkeypatch):
    monkeypatch.setattr(httpx, "get", lambda *a, **k: _Resp(404, {}))
    assert wikipedia_tool.scrape_detailed_synopsis("Zzzz") is None

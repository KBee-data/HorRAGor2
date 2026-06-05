"""Test du tool query_movie_metadata — repository injecte (pas de base reelle)."""

from backend.config import settings
from backend.contracts.schemas import FilmMetadata
from backend.tools import sql_tool


class _FakeRepo:
    def get_metadata(self, film_id: int) -> FilmMetadata | None:
        if film_id == 1:
            return FilmMetadata(id=1, title="The Thing", release_year=1982, genres=["Horror"])
        if film_id == 2:
            return FilmMetadata(id=2, tmdb_id=493, title="Hereditary", genres=["Horror"])
        return None


def test_query_movie_metadata_found():
    sql_tool.set_repository(_FakeRepo())
    md = sql_tool.query_movie_metadata(1)
    assert md is not None
    assert md.title == "The Thing"
    assert md.genres == ["Horror"]


def test_query_movie_metadata_absent():
    sql_tool.set_repository(_FakeRepo())
    assert sql_tool.query_movie_metadata(999) is None


def test_query_movie_metadata_enriches_via_tmdb(monkeypatch):
    sql_tool.set_repository(_FakeRepo())
    monkeypatch.setattr(settings, "tmdb_token", "dummy")  # active l'enrichissement
    monkeypatch.setattr(
        sql_tool.tmdb,
        "get_credits",
        lambda tmdb_id, **k: {"director": "Ari Aster", "cast": ["Toni Collette"]},
    )
    md = sql_tool.query_movie_metadata(2)  # film_id 2 a un tmdb_id
    assert md.director == "Ari Aster"
    assert md.cast == ["Toni Collette"]


def test_query_movie_metadata_no_enrich_without_tmdb_id(monkeypatch):
    sql_tool.set_repository(_FakeRepo())
    monkeypatch.setattr(settings, "tmdb_token", "dummy")
    # film_id 1 n'a pas de tmdb_id -> pas d'appel TMDB
    monkeypatch.setattr(
        sql_tool.tmdb, "get_credits",
        lambda *a, **k: (_ for _ in ()).throw(AssertionError("ne doit pas etre appele")),
    )
    md = sql_tool.query_movie_metadata(1)
    assert md.director is None and md.cast == []

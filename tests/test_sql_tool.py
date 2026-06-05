"""Test du tool query_movie_metadata — repository injecte (pas de base reelle)."""

from backend.contracts.schemas import FilmMetadata
from backend.tools import sql_tool


class _FakeRepo:
    def get_metadata(self, film_id: int) -> FilmMetadata | None:
        if film_id == 1:
            return FilmMetadata(id=1, title="The Thing", release_year=1982, genres=["Horror"])
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

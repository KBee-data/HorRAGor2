"""Tests du tool find_similar_horror_movies.

- unitaire : repository factice (CI-safe, pas de base) ;
- integration : reco reelle, SKIP si pas de DATABASE_URL (ex. en CI).
"""

import pytest
from sqlalchemy import text

from backend.config import settings
from backend.contracts.schemas import FilmRef
from backend.tools import pgvector_tool


class _FakeRepo:
    def recommend_similar(self, film_id: int, k: int = 5) -> list[FilmRef]:
        return [FilmRef(id=10, title="Alien"), FilmRef(id=20, title="The Thing")][:k]


def test_find_similar_delegates_to_repository():
    pgvector_tool.set_repository(_FakeRepo())
    out = pgvector_tool.find_similar_horror_movies(1, k=2)
    assert [r.title for r in out] == ["Alien", "The Thing"]


@pytest.mark.skipif(not settings.database_url, reason="DATABASE_URL absente (pas de base)")
def test_find_similar_integration():
    from backend.data.db import get_engine

    pgvector_tool.set_repository(None)  # force le repo reel (Supabase)
    with get_engine().connect() as conn:
        seed = conn.execute(text("select movie_id from movie_embeddings limit 1")).scalar()
    if seed is None:
        pytest.skip("aucun embedding en base (lancer horragor-embeddings)")
    out = pgvector_tool.find_similar_horror_movies(seed, k=5)
    assert isinstance(out, list) and len(out) <= 5
    assert all(isinstance(r, FilmRef) for r in out)

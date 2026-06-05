"""Connecteur SQL securise : fonctions Python typees au-dessus de la base.

REGLE D'OR (brief) : le LLM ne genere JAMAIS de SQL. Toutes les requetes vivent ICI,
**parametrees** (pas d'injection possible), et renvoient des objets types (FilmMetadata).

Mapping vers le schema reel de Part 1 :
- annee  <- movies.release_date (DATE)
- genres <- jointure movie_genres / genres (multi-valeurs)
- rating <- table ratings (echelle 0-10 : imdb prioritaire, sinon tmdb)
- synopsis <- movies.overview
- realisateur / casting : ABSENTS de la base -> enrichis via TMDB (etape suivante).
"""

from datetime import date

from sqlalchemy import Engine, text

from backend.contracts.schemas import FilmMetadata, FilmRef
from backend.data.db import get_engine


def _year_from(value) -> int | None:
    """Annee depuis une date (Postgres -> date) ou une chaine ISO (SQLite -> 'YYYY-..')."""
    if value is None:
        return None
    if isinstance(value, date):
        return value.year
    head = str(value)[:4]
    return int(head) if head.isdigit() else None


def _pick_rating(rows: list[tuple[str, float | None]]) -> float | None:
    """Choisit une note sur 0-10 : imdb puis tmdb (RT est en 0-100 -> ignore ici)."""
    scores = {src: score for src, score in rows}
    for source in ("imdb", "tmdb"):
        if scores.get(source) is not None:
            return float(scores[source])
    return None


class SupabaseFilmRepository:
    """Implementation SQL de contracts.interfaces.FilmRepository."""

    def __init__(self, engine: Engine | None = None):
        # Engine injectable (tests sur SQLite local) ; sinon engine partage (Supabase).
        self._engine = engine or get_engine()

    def get_metadata(self, film_id: int) -> FilmMetadata | None:
        with self._engine.connect() as conn:
            movie = conn.execute(
                text(
                    "select id, tmdb_id, title, release_date, overview "
                    "from movies where id = :id"
                ),
                {"id": film_id},
            ).first()
            if movie is None:
                return None
            genres = [
                name
                for (name,) in conn.execute(
                    text(
                        "select g.name from genres g "
                        "join movie_genres mg on mg.genre_id = g.id "
                        "where mg.movie_id = :id order by g.name"
                    ),
                    {"id": film_id},
                ).all()
            ]
            rating = _pick_rating(
                conn.execute(
                    text("select source, score from ratings where movie_id = :id"),
                    {"id": film_id},
                ).all()
            )
        return FilmMetadata(
            id=movie.id,
            tmdb_id=movie.tmdb_id,
            title=movie.title,
            release_year=_year_from(movie.release_date),
            genres=genres,
            rating=rating,
            synopsis=movie.overview,
            # director / cast : enrichis via TMDB dans le tool query_movie_metadata
        )

    def validate_film(self, title: str) -> FilmRef | None:
        # La validation floue est assuree par le routeur FAISS (backend.tools.faiss_tool).
        raise NotImplementedError("Utiliser backend.tools.faiss_tool.validate_film.")

    def recommend_similar(self, film_id: int, k: int = 5) -> list[FilmRef]:
        # Necessite la decision "stockage des embeddings" (pgvector) — a venir.
        raise NotImplementedError("Reco pgvector : en attente de la decision embeddings.")

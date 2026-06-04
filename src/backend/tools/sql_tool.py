"""Tool 1 — query_movie_metadata : metadonnees de base d'un film.

Renvoie realisateur, annee, genre, note moyenne, casting. C'est la SEULE source
autorisee pour ces faits (obligation d'utiliser les donnees brutes -> 0 hallucination).
"""

from backend.contracts.schemas import FilmMetadata


def query_movie_metadata(film_id: int) -> FilmMetadata:
    """Renvoie les metadonnees brutes via le connecteur SQL securise."""
    # TODO (temps 2) : appeler backend.data.db.SupabaseFilmRepository.get_metadata
    raise NotImplementedError

"""Tool 1 — query_movie_metadata : metadonnees de base d'un film.

Renvoie realisateur, annee, genres, note, casting, synopsis. C'est la SEULE source
autorisee pour ces faits (obligation d'utiliser les donnees brutes -> 0 hallucination).

Le tool ne fait que deleguer au connecteur SQL securise (SupabaseFilmRepository) :
le LLM appelle ce tool, jamais la base directement.
"""

from backend.contracts.interfaces import FilmRepository
from backend.contracts.schemas import FilmMetadata
from backend.data.repository import SupabaseFilmRepository

_repository: FilmRepository | None = None


def set_repository(repository: FilmRepository) -> None:
    """Injecte le repository (au demarrage de l'API, ou un fake en test)."""
    global _repository
    _repository = repository


def _get_repository() -> FilmRepository:
    global _repository
    if _repository is None:
        _repository = SupabaseFilmRepository()  # connexion Supabase paresseuse
    return _repository


def query_movie_metadata(film_id: int) -> FilmMetadata | None:
    """Renvoie les metadonnees brutes du film, ou None s'il n'existe pas."""
    return _get_repository().get_metadata(film_id)

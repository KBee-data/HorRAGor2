"""Tool 2 — find_similar_horror_movies : recommandation de films proches.

POURQUOI pgvector (et pas FAISS) : on cherche une similarite de CONTENU (synopsis),
pas une validation d'identifiant. On passe l'id d'un film et on recupere les k films
les plus proches par similarite cosinus sur les vecteurs de synopsis.

Le tool delegue au connecteur (SupabaseFilmRepository), via un singleton injectable
(meme pattern que sql_tool) : le LLM appelle le tool, jamais la base directement.
"""

from backend.contracts.interfaces import FilmRepository
from backend.contracts.schemas import FilmRef
from backend.data.repository import SupabaseFilmRepository

_repository: FilmRepository | None = None


def set_repository(repository: FilmRepository) -> None:
    """Injecte le repository (au demarrage de l'API, ou un fake en test)."""
    global _repository
    _repository = repository


def _get_repository() -> FilmRepository:
    global _repository
    if _repository is None:
        _repository = SupabaseFilmRepository()
    return _repository


def find_similar_horror_movies(film_id: int, k: int = 5) -> list[FilmRef]:
    """Renvoie les k films les plus proches semantiquement (vide si film sans embedding)."""
    return _get_repository().recommend_similar(film_id, k)

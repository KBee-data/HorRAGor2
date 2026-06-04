"""Tool 2 — find_similar_horror_movies : recommandation de films proches.

POURQUOI pgvector (et pas FAISS) : on cherche une similarite de CONTENU (synopsis),
pas une simple validation d'ID. On passe un ID de film et on recupere les k films
les plus proches par similarite cosinus sur les vecteurs de synopsis.
"""

from backend.contracts.schemas import FilmRef


def find_similar_horror_movies(film_id: int, k: int = 5) -> list[FilmRef]:
    """Renvoie les k films les plus proches semantiquement via pgvector."""
    # TODO (temps 2) : appeler backend.data.db.SupabaseFilmRepository.recommend_similar
    raise NotImplementedError

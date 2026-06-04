"""Connecteur SQL securise vers Supabase.

REGLE D'OR (PDF) : le LLM ne genere JAMAIS de SQL brut. Tout passe par des
fonctions Python typees, ici. Cette classe implementera le contrat `FilmRepository`.

POURQUOI une classe (et pas des fonctions libres) : encapsule le client Supabase
(initialise une seule fois avec les cles confinees au Back-End) et expose une API
stable que les tools consomment sans connaitre les details SQL.
"""

from backend.contracts.schemas import FilmMetadata, FilmRef


class SupabaseFilmRepository:
    """Implementation reelle de FilmRepository (a completer par C)."""

    def __init__(self) -> None:
        # TODO : initialiser le client Supabase depuis backend.config.settings
        ...

    def validate_film(self, title: str) -> FilmRef | None:
        # TODO : valider via l'index FAISS (titres) -> renvoyer l'id
        raise NotImplementedError

    def get_metadata(self, film_id: int) -> FilmMetadata:
        # TODO : SELECT parametre sur la table films (requete prete, jamais generee par le LLM)
        raise NotImplementedError

    def recommend_similar(self, film_id: int, k: int = 5) -> list[FilmRef]:
        # TODO : recherche de similarite cosinus via pgvector
        raise NotImplementedError

"""Interfaces (contrats de comportement) entre les briques.

POURQUOI des `Protocol` plutot que des classes de base abstraites :
- duck typing statique : une classe est compatible si elle a les bonnes methodes,
  sans heritage explicite -> couplage minimal entre les briques ;
- l'API depend de l'ABSTRACTION `AgentEngine`, pas d'une implementation concrete.
  On branche d'abord le mock, puis le vrai agent, SANS toucher au code de l'API.
"""

from typing import Protocol

from backend.contracts.schemas import ChatRequest, ChatResponse, FilmMetadata, FilmRef


class AgentEngine(Protocol):
    """Ce que l'API appelle pour obtenir une reponse (mock, puis vrai agent)."""

    async def run(self, req: ChatRequest) -> ChatResponse: ...


class FilmRepository(Protocol):
    """Acces aux donnees cote brique data (implemente par Supabase + FAISS).

    Les tools de l'agent s'appuient sur cette interface : ils n'ecrivent jamais
    de SQL eux-memes (regle de securite du PDF).
    """

    def validate_film(self, title: str) -> FilmRef | None: ...

    def get_metadata(self, film_id: int) -> FilmMetadata: ...

    def recommend_similar(self, film_id: int, k: int = 5) -> list[FilmRef]: ...

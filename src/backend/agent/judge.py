"""Nœud Juge DETERMINISTE (temps 2).

POURQUOI deterministe (du code, pas un 2e appel LLM) pour les metadonnees de base :
on vise 0% d'hallucination sur realisateur/annee/genre. Un second LLM pourrait
lui-meme se tromper ; une verification litterale "le fait cite est-il dans les
observations des tools ?" est fiable, gratuite et reproductible.
"""

from backend.contracts.schemas import ChatResponse, FilmMetadata


def verify(answer: str, metadata: FilmMetadata) -> bool:
    """Renvoie True si la reponse est fidele aux donnees brutes, False sinon."""
    # TODO (temps 2) : verification litterale des faits cites contre `metadata`
    raise NotImplementedError


def fallback() -> ChatResponse:
    """Reponse polie quand l'information est introuvable / non verifiable.

    POURQUOI une reponse dediee : le critere du PDF impose d'admettre l'ignorance
    plutot que d'inventer. On renvoie un message neutre et trace (verdict=fallback).
    """
    return ChatResponse(
        answer="Desole, je ne dispose pas de cette information de maniere fiable.",
        sources=[],
        verdict="fallback",
    )

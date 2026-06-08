"""Registre des outils LangChain exposes a l'agent.

CHOIX DE CONCEPTION (fiabilite avec un petit modele) : les outils sont **par titre**.
Un petit LLM (llama3.2:3b) chaine mal "valider le titre -> recuperer l'id -> interroger
par id". On compose donc ces etapes EN INTERNE : le modele n'appelle qu'un outil avec un
titre et recoit directement les faits. Les fonctions data sous-jacentes (validate_film,
query_movie_metadata, find_similar_horror_movies, calculate_movie_age, scrape_...) restent
celles de la brique data (conformes au brief) ; on les orchestre ici.

Les outils ne LEVENT jamais d'exception (ils renvoient {"found": false} / []) : le LLM
recoit des observations propres plutot que des erreurs.
"""

from langchain_core.tools import tool

from backend import trace
from backend.tools import faiss_tool, pgvector_tool, sql_tool, temporal_tool, wikipedia_tool


@tool
def lookup_movie(title: str) -> dict:
    """Recherche un film d'horreur par son TITRE et renvoie ses faits.

    Renvoie realisateur, annee, genres, note, casting, synopsis. A utiliser pour TOUTE
    question factuelle sur un film. Si le film est inconnu, renvoie {"found": false}
    (dans ce cas, repondre poliment qu'on ne connait pas ce film).
    """
    trace.record("tool", "lookup_movie", f"titre={title!r}")
    ref = faiss_tool.validate_film(title)
    if ref is None:
        return {"found": False}
    metadata = sql_tool.query_movie_metadata(ref.id)
    if metadata is None:
        return {"found": False}
    data = metadata.model_dump()
    data["found"] = True
    return data


@tool
def find_similar(title: str, k: int = 5) -> list[dict]:
    """Recommande k films d'horreur proches d'un film donne par son TITRE (vide si inconnu)."""
    trace.record("tool", "find_similar", f"titre={title!r}, k={k}")
    ref = faiss_tool.validate_film(title)
    if ref is None:
        return []
    return [r.model_dump() for r in pgvector_tool.find_similar_horror_movies(ref.id, k)]


@tool
def movie_age(title: str) -> dict:
    """Calcule l'age (en annees) d'un film d'horreur, par son TITRE.

    Va chercher l'annee de sortie EN BASE (on ne fait jamais confiance a une annee
    fournie par toi). Renvoie {"found": false} si le film est inconnu.
    """
    trace.record("tool", "movie_age", f"titre={title!r}")
    ref = faiss_tool.validate_film(title)
    if ref is None:
        return {"found": False}
    metadata = sql_tool.query_movie_metadata(ref.id)
    if metadata is None or metadata.release_year is None:
        return {"found": False}
    age = temporal_tool.calculate_movie_age(metadata.release_year)
    return {
        "found": True,
        "title": metadata.title,
        "release_year": metadata.release_year,
        "age": age,
    }


@tool
def wikipedia_synopsis(title: str) -> str | None:
    """Synopsis detaille depuis Wikipedia.

    A N'UTILISER QUE si l'utilisateur demande des details/anecdotes approfondis introuvables
    dans les faits de la base. Renvoie null si rien trouve.
    """
    trace.record("tool", "wikipedia_synopsis", f"titre={title!r}")
    return wikipedia_tool.scrape_detailed_synopsis(title)


TOOLS = [lookup_movie, find_similar, movie_age, wikipedia_synopsis]

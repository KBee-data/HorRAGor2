"""Registre des outils LangChain exposes a l'agent (temps 2).

Chaque outil enveloppe une fonction data deja testee (faiss/sql/pgvector/temporal/wiki)
et renvoie des donnees JSON-serialisables (dict/list/str) pour que le LLM les lise
proprement. Les docstrings sont IMPORTANTES : elles indiquent au modele QUAND utiliser
chaque outil (orchestration ReAct).
"""

from langchain_core.tools import tool

from backend.tools import faiss_tool, pgvector_tool, sql_tool, temporal_tool, wikipedia_tool


@tool
def validate_film(title: str) -> dict | None:
    """Valide qu'un film d'horreur existe et renvoie son identifiant (id) et son titre exact.

    A APPELER EN PREMIER quand l'utilisateur parle d'un film : les autres outils ont besoin
    de l'id. Renvoie null si le film n'est pas dans la base (alors : repondre qu'on ne sait pas).
    """
    ref = faiss_tool.validate_film(title)
    return ref.model_dump() if ref else None


@tool
def query_movie_metadata(film_id: int) -> dict | None:
    """Donne les FAITS d'un film via son id : realisateur, annee, genres, note, casting, synopsis.

    Source de verite pour toute question factuelle (ne jamais inventer ces valeurs).
    """
    md = sql_tool.query_movie_metadata(film_id)
    return md.model_dump() if md else None


@tool
def find_similar_horror_movies(film_id: int, k: int = 5) -> list[dict]:
    """Recommande k films d'horreur semantiquement proches d'un film (par son id)."""
    return [ref.model_dump() for ref in pgvector_tool.find_similar_horror_movies(film_id, k)]


@tool
def calculate_movie_age(release_year: int) -> int:
    """Calcule l'age d'un film (en annees) a partir de son annee de sortie."""
    return temporal_tool.calculate_movie_age(release_year)


@tool
def scrape_detailed_synopsis(title: str) -> str | None:
    """Recupere un synopsis detaille depuis Wikipedia.

    A N'UTILISER QUE si l'utilisateur demande des details/anecdotes approfondis introuvables
    dans les metadonnees de la base. Renvoie null si rien trouve.
    """
    return wikipedia_tool.scrape_detailed_synopsis(title)


# Liste passee a l'agent (bind_tools) et au ToolNode.
TOOLS = [
    validate_film,
    query_movie_metadata,
    find_similar_horror_movies,
    calculate_movie_age,
    scrape_detailed_synopsis,
]

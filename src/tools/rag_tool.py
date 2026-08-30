"""Native RAG tool for local FAISS title matching and structured database lore extraction.

Handles:
1. Fuzzy vector title matching via FAISS (TitleIndex).
2. SQL metadata retrieval (director, year, genres, rating, cast, synopsis).
3. PGVector recommendations for similar horror films.
"""

from typing import Any
from backend.tools import faiss_tool, pgvector_tool, sql_tool


def search_local_rag(title_query: str) -> dict[str, Any]:
    """Searches the local FAISS index for a movie title and extracts its database facts.

    Args:
        title_query: The raw movie title or user search term.

    Returns:
        A dictionary containing matched movie details and metadata, or found=False.
    """
    # 1. Fuzzy vector title matching via FAISS
    ref = faiss_tool.validate_film(title_query)
    if ref is None:
        return {"found": False, "title": None, "query": title_query}

    # 2. SQL metadata retrieval (shielded against database connection failures)
    try:
        metadata = sql_tool.query_movie_metadata(ref.id)
    except Exception:
        metadata = None

    if metadata is None:
        return {
            "found": False,
            "title": ref.title,
            "matched_title": ref.title,
            "query": title_query,
            "has_synopsis": False,
        }

    data = metadata.model_dump()
    data["found"] = True
    data["matched_title"] = ref.title

    # 3. PGVector recommendations (shielded)
    try:
        similar = pgvector_tool.find_similar_horror_movies(ref.id, k=5)
        data["similar_movies"] = [m.title for m in similar]
    except Exception:
        data["similar_movies"] = []

    # 4. Check whether local synopsis is present and substantive
    synopsis = data.get("synopsis") or ""
    data["has_synopsis"] = len(synopsis.strip()) > 30

    return data

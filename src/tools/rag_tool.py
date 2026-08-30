"""Native RAG tool for local FAISS title matching and structured database lore extraction.

Handles:
1. Fuzzy vector title matching via FAISS (TitleIndex).
2. SQL metadata retrieval (director, year, genres, rating, cast, synopsis).
3. PGVector recommendations for similar horror films.
"""

import re
from typing import Any
from backend.tools import faiss_tool, pgvector_tool, sql_tool


def _extract_candidate_title(query: str, active_title: str | None = None) -> str:
    """Extracts likely movie title from conversational questions in English or French.

    If the query uses pronouns/anaphora ('it', 'this movie', 'ce film', 'il') and an
    active_title from a previous turn is available, resolves to active_title.
    """
    q = query.strip()
    # 1. Check for quoted text: "The Thing" or 'The Thing'
    quoted = re.findall(r'["\']([^"\']+)["\']', q)
    if quoted:
        return quoted[0].strip()

    # 2. Check if the question is anaphoric (referencing previously established movie)
    anaphora_patterns = [
        r"\b(?:it|this movie|this film|that movie|that film)\b",
        r"\b(?:ce film|ce chef-d'œuvre|cette œuvre|il|elle|lui|dedans|son|sa|ses)\b",
    ]
    is_anaphoric = any(re.search(pat, q, flags=re.IGNORECASE) for pat in anaphora_patterns)

    # 3. Strip common conversational question prefixes
    patterns = [
        r"^(?:who directed|who is the director of|who made|what is the plot of|what is the story of|tell me about|what about|synopsis of|anecdotes about|trivia about|what year was|when was)\s+",
        r"^(?:qui a réalisé|quel est le réalisateur de|qui a fait|que raconte|de quoi parle|parle-moi de|donne-moi des infos sur|synopsis de|anecdotes sur|en quelle année est|quand est)\s+",
        r"^(?:the film|the movie|le film|l'œuvre)\s+",
    ]
    cleaned = q
    for pat in patterns:
        cleaned = re.sub(pat, "", cleaned, flags=re.IGNORECASE).strip()

    cleaned = re.sub(r"[?!.]+$", "", cleaned).strip()

    # If the user explicitly used an anaphoric reference ('it', 'this movie', 'il') or if cleaned became empty
    if active_title and (is_anaphoric or not cleaned):
        return active_title

    return cleaned if cleaned else (active_title or q)


def search_local_rag(title_query: str, active_title: str | None = None) -> dict[str, Any]:
    """Searches the local FAISS index for a movie title and extracts its database facts.

    Args:
        title_query: The raw movie title or user search term.
        active_title: Active movie title from previous conversational turn.

    Returns:
        A dictionary containing matched movie details and metadata, or found=False.
    """
    candidate = _extract_candidate_title(title_query, active_title=active_title)

    # 1. Fuzzy vector title matching via FAISS (try extracted title first, fallback to raw query)
    ref = faiss_tool.validate_film(candidate)
    if ref is None and candidate != title_query:
        ref = faiss_tool.validate_film(title_query)

    if ref is None:
        # If FAISS couldn't validate and we had an active title, retain active_title for web scraper
        effective_title = active_title if active_title else candidate
        return {"found": False, "title": effective_title, "matched_title": None, "query": title_query}

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

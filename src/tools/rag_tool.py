"""Native RAG tool for local FAISS title matching and structured database lore extraction.

Handles:
1. Fuzzy vector title matching via FAISS (TitleIndex).
2. SQL metadata retrieval (director, year, genres, rating, cast, synopsis).
3. PGVector recommendations for similar horror films.
"""

import json
import logging
import re
from typing import Any
import httpx

from backend.tools import faiss_tool, pgvector_tool, sql_tool
from src.config import settings

logger = logging.getLogger(__name__)


def _extract_entities_llm(query: str) -> tuple[str | None, str | None, int | None]:
    """Uses local LLM to extract movie title, director, and year in structured JSON."""
    try:
        url = f"{settings.ollama_base_url.rstrip('/')}/api/generate"
        prompt = (
            "You are a movie entity extraction system. Identify the movie title, "
            "director (if mentioned), and release year (if mentioned) from the user query.\n"
            "If the user asks about a sequel (e.g. Scary Movie 3), include the number in the title.\n"
            "Return JSON matching: {\"title\": \"<extracted title or null>\", \"director\": \"<director or null>\", \"year\": <year as int or null>}\n\n"
            f"User query: \"{query}\""
        )
        payload = {
            "model": settings.llm_model,
            "prompt": prompt,
            "format": "json",
            "stream": False,
            "options": {"temperature": 0.0, "num_predict": 60},
        }
        with httpx.Client(timeout=3.0) as client:
            resp = client.post(url, json=payload)
            if resp.status_code == 200:
                raw_json = resp.json().get("response", "{}")
                data = json.loads(raw_json)
                title = data.get("title")
                director = data.get("director")
                year = data.get("year")
                if isinstance(year, str) and year.isdigit():
                    year = int(year)
                elif not isinstance(year, int):
                    year = None

                if title and str(title).strip().lower() not in ("null", "none", ""):
                    clean_title = str(title).strip()
                    clean_dir = (
                        str(director).strip()
                        if director and str(director).strip().lower() not in ("null", "none", "")
                        else None
                    )
                    return clean_title, clean_dir, year
    except Exception as exc:
        logger.debug(f"LLM entity extraction skipped/failed: {exc}")
    return None, None, None


def extract_query_constraints(query: str, active_title: str | None = None) -> tuple[str, str | None, int | None]:
    """Extracts movie title and optional director/year constraints from conversational queries.

    Employs a two-layer extraction strategy:
    1. Zero-shot LLM Entity Extraction via local Ollama (resilient against arbitrary phrasing and typos).
    2. Deterministic NLP / Regex fallback (instant execution for offline tests and simple queries).

    Returns:
        tuple of (clean_candidate_title, specified_director, specified_year)
    """
    q = query.strip()

    # 1. Fast path: Quoted text takes immediate precedence ("The Thing")
    quoted = re.findall(r'["\']([^"\']+)["\']', q)
    quoted_title = quoted[0].strip() if quoted else None

    # 2. Check if the question is anaphoric ('it', 'this movie', 'ce film', 'il')
    anaphora_patterns = [
        r"\b(?:it|this movie|this film|that movie|that film)\b",
        r"\b(?:ce film|ce chef-d'œuvre|cette œuvre|il|elle|lui|dedans|son|sa|ses)\b",
    ]
    is_anaphoric = any(re.search(pat, q, flags=re.IGNORECASE) for pat in anaphora_patterns)

    # 3. Deterministic constraint extraction for director & year
    m_dir = re.search(
        r'\b(?:directed by|réalisé par|is the director of)\s+([A-Za-zÀ-ÿ\s\-\.\']+?)(?:\s+(?:in|released in|sorti en|from)\s+\d{4}|[?!,.]|$)',
        q,
        flags=re.IGNORECASE,
    )
    specified_director = m_dir.group(1).strip() if m_dir else None

    m_year = re.search(r'\b(?:released in|sorti en|from|year|année|de|in)\s+(\d{4})\b', q, flags=re.IGNORECASE)
    specified_year = int(m_year.group(1)) if m_year else None

    if active_title and is_anaphoric:
        return active_title, specified_director, specified_year

    if quoted_title:
        return quoted_title, specified_director, specified_year

    # 4. Layer 1: Zero-shot LLM Entity Extraction
    llm_title, llm_dir, llm_year = _extract_entities_llm(q)
    if llm_title:
        final_dir = llm_dir or specified_director
        final_year = llm_year or specified_year
        return llm_title, final_dir, final_year

    # 5. Layer 2: Robust Deterministic NLP Fallback
    cleaned = q

    # Strip trailing director/year clauses from title string
    cleaned = re.sub(r"\b(?:directed by|réalisé par)\s+.*$", "", cleaned, flags=re.IGNORECASE).strip()
    cleaned = re.sub(r"\b(?:released in|sorti en|from)\s+\d{4}.*$", "", cleaned, flags=re.IGNORECASE).strip()
    cleaned = re.sub(r"[?!.,]+$", "", cleaned).strip()

    # Iterative prefix stripping (handles questions + descriptors like "what can you tell me about" + "the comedy")
    prefixes = [
        r"^(?:what can you tell me about|can you tell me about|could you tell me about|what do you know about|do you know anything about)\s+",
        r"^(?:tell me all about|tell me more about|tell me about|what about|synopsis of|anecdotes about|trivia about)\s+",
        r"^(?:who directed|who is the director of|who made|what is the plot of|what is the story of|what is the synopsis of|what year was|when was)\s+",
        r"^(?:que peux-tu me dire sur|peux-tu me parler de|peux-tu me dire|parle-moi de|dis-moi tout sur|donne-moi des infos sur)\s+",
        r"^(?:qui a réalisé|quel est le réalisateur de|qui a fait|que raconte|de quoi parle|synopsis de|anecdotes sur|en quelle année est|quand est)\s+",
        r"^(?:the comedy|the horror movie|the horror film|the movie|the film|the parody|the slasher|the feature film)\s+",
        r"^(?:le film d[\'\"]horreur|le film|la comédie|la parodie|l[\'\"]œuvre)\s+",
    ]

    changed = True
    while changed:
        changed = False
        for pat in prefixes:
            new_cleaned = re.sub(pat, "", cleaned, flags=re.IGNORECASE).strip()
            if new_cleaned != cleaned:
                cleaned = new_cleaned
                changed = True

    if active_title and not cleaned:
        return active_title, specified_director, specified_year

    title = cleaned if cleaned else (active_title or q)
    return title, specified_director, specified_year


def _extract_candidate_title(query: str, active_title: str | None = None) -> str:
    """Extracts likely movie title from conversational questions in English or French."""
    title, _, _ = extract_query_constraints(query, active_title=active_title)
    return title


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

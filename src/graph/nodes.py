"""Node functions for the HorRAGor Multi-Agent LangGraph architecture.

Contains:
1. rag_node: Local researcher extracting FAISS vector matches & DB lore.
2. scraper_node: Web investigator scraping live Wikipedia data when local lore is insufficient.
3. narration_node: Gothic horror storyteller with strict context trimming & isolation.
"""

import re
from typing import Any
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_ollama import ChatOllama

from src.config import settings
from src.models.state import HorragorState
from src.tools.rag_tool import (
    _extract_candidate_title,
    extract_query_constraints,
    search_local_rag,
)
from src.tools.scraper_tool import scrape_web_synopsis

# --- LLM Instances ---
def _get_narration_llm() -> ChatOllama:
    """Returns Ollama LLM configured for atmospheric gothic storytelling."""
    return ChatOllama(
        model=settings.llm_model,
        base_url=settings.ollama_base_url,
        temperature=settings.narration_temperature,
    )


# --- Node 1: RAG Agent (Local Researcher) ---
def rag_node(state: HorragorState) -> dict[str, Any]:
    """Interrogates local FAISS index and structured DB to extract raw horror facts."""
    query = state.get("query", "").strip()
    sources = list(state.get("sources") or [])
    active_title = state.get("active_title")

    candidate_title, spec_dir, spec_year = extract_query_constraints(query, active_title=active_title)
    rag_result = search_local_rag(query, active_title=active_title)

    matched_title = rag_result.get("matched_title") or rag_result.get("title")
    extracted_title = matched_title or candidate_title or active_title

    # 1. Detect sequel / number mismatch (e.g. user asked for 'Scary Movie 3' but FAISS returned 'Scary Movie')
    sequel_mismatch = False
    if candidate_title and matched_title:
        q_nums = set(re.findall(r"\b(?:\d+|[ivx]+)\b", candidate_title.lower()))
        m_nums = set(re.findall(r"\b(?:\d+|[ivx]+)\b", matched_title.lower()))
        if q_nums and q_nums != m_nums:
            sequel_mismatch = True
            extracted_title = candidate_title  # Forward exact sequel title to Scraper Agent

    # 2. Detect director contradiction (e.g. user asked for 'Keenan Ivory Wayans' but DB has 'Daniel Erickson')
    director_mismatch = False
    if spec_dir and rag_result.get("director"):
        local_dir = str(rag_result["director"]).lower()
        dir_tokens = [t.lower() for t in re.findall(r"[A-Za-zÀ-ÿ]+", spec_dir) if len(t) > 2]
        if dir_tokens and not any(t in local_dir for t in dir_tokens):
            director_mismatch = True
            extracted_title = candidate_title

    # 3. Detect release year contradiction (e.g. user asked for '2000' but DB has '1991')
    year_mismatch = False
    if spec_year and rag_result.get("release_year"):
        try:
            local_year = int(rag_result["release_year"])
            if abs(spec_year - local_year) > 1:
                year_mismatch = True
                extracted_title = candidate_title
        except (ValueError, TypeError):
            pass

    has_mismatch = sequel_mismatch or director_mismatch or year_mismatch

    if rag_result.get("found") and not has_mismatch:
        sources.append("FAISS Vector Index")
        sources.append("Local Horror DB")
        has_synopsis = rag_result.get("has_synopsis", False)
        is_sufficient = bool(has_synopsis)
    else:
        if extracted_title and not has_mismatch:
            sources.append("FAISS Vector Index")
        is_sufficient = False

    return {
        "extracted_title": extracted_title,
        "active_title": extracted_title,
        "rag_data": rag_result if not has_mismatch else {},
        "is_local_info_sufficient": is_sufficient,
        "sources": sorted(set(sources)),
    }


# --- Node 2: Scraper Agent (Web Investigator) ---
def scraper_node(state: HorragorState) -> dict[str, Any]:
    """Scrapes live Wikipedia data when local facts are missing or incomplete."""
    sources = list(state.get("sources") or [])
    target_title = state.get("extracted_title") or state.get("query", "").strip()

    web_result = scrape_web_synopsis(target_title)
    if web_result.get("found"):
        sources.append("Wikipedia Web Scraper")
        web_content = str(web_result.get("content", ""))
    else:
        web_content = f"Aucune information supplémentaire trouvée sur le web pour '{target_title}'."

    return {
        "web_data": web_content,
        "sources": sorted(set(sources)),
    }


# --- Context Trimming Helper ---
def _build_context_summary(state: HorragorState) -> str:
    """Builds a clean, trimmed factual summary free of technical logs or schema bloat."""
    rag_data = state.get("rag_data") or {}
    web_data = state.get("web_data") or ""
    query = state.get("query", "")

    lines = []
    matched_title = rag_data.get("matched_title") or rag_data.get("title")
    if matched_title:
        lines.append(f"- Titre de l'œuvre : {matched_title}")

    if rag_data.get("found"):
        if rag_data.get("director"):
            lines.append(f"- Réalisateur : {rag_data.get('director')}")
        if rag_data.get("release_year"):
            lines.append(f"- Année de sortie : {rag_data.get('release_year')}")
        if rag_data.get("genres"):
            genres = ", ".join(rag_data.get("genres")) if isinstance(rag_data.get("genres"), list) else rag_data.get("genres")
            lines.append(f"- Genres : {genres}")
        if rag_data.get("vote_average"):
            lines.append(f"- Note du public : {rag_data.get('vote_average')}/10")
        if rag_data.get("cast"):
            cast = ", ".join(rag_data.get("cast")[:5]) if isinstance(rag_data.get("cast"), list) else rag_data.get("cast")
            lines.append(f"- Distribution / Acteurs : {cast}")
        if rag_data.get("synopsis"):
            lines.append(f"- Synopsis local : {rag_data.get('synopsis')}")
        if rag_data.get("similar_movies"):
            similar = ", ".join(rag_data.get("similar_movies")[:5])
            lines.append(f"- Recommandations de films similaires : {similar}")
    elif not matched_title:
        lines.append(f"- Recherche locale : Aucun film correspondant exactement trouvé pour la requête '{query}'.")

    if web_data:
        lines.append(f"- Informations du Web (Wikipedia) : {web_data}")

    return "\n".join(lines)


# --- Node 3: Narration Agent (Gothic Writer) ---
GOTHIC_PROMPT = """\
Tu es l'Écrivain Gothique de HorRAGor, une entité littéraire et ténébreuse spécialisée dans l'horreur et le cinéma d'épouvante.

MISSION :
Réponds directement à la question de l'utilisateur en transformant la synthèse brute des données en un récit captivant, immersif et teinté d'une atmosphère d'épouvante (style gothique, Edgar Allan Poe, H.P. Lovecraft).

RÈGLES STRICTES :
1. RESPECT DES FAITS : Base-toi UNIQUEMENT sur les faits fournis dans la SYNTHÈSE DES DONNÉES. Ne contredis JAMAIS les faits et n'invente rien.
2. CONCISION (TRÈS IMPORTANT) : Reste concis et percutant (1 à 2 paragraphes maximum). Réponds directement à la question sans longueurs superflues.
3. DONNÉES ABSENTES / FILM INCONNU : Si la synthèse indique qu'aucune information n'a été trouvée ou que l'œuvre est inconnue, réponds en UNE SEULE phrase brève et mystérieuse (ex: "The cursed archives hold no records of this title." / "Les archives de l'ombre restent muettes sur cette œuvre."). Ne brode JAMAIS de longs paragraphes si les données sont absentes.
4. LANGUE : Réponds impérativement dans la même langue que celle de l'utilisateur (anglais si la question est en anglais, français si elle est en français).
"""


def narration_node(state: HorragorState) -> dict[str, Any]:
    """Generates the atmospheric gothic narrative using trimmed, isolated context."""
    query = state.get("query", "")
    context_summary = _build_context_summary(state)

    llm = _get_narration_llm()
    prompt_messages = [
        SystemMessage(content=GOTHIC_PROMPT),
        HumanMessage(
            content=(
                f"QUESTION DE L'UTILISATEUR :\n{query}\n\n"
                f"SYNTHÈSE DES DONNÉES BRUTES (FAITS STRICTS) :\n{context_summary}\n\n"
                "Rédige ta réponse dans ton style gothique et immersif en restituant fidèlement les faits."
            )
        ),
    ]

    response = llm.invoke(prompt_messages)
    final_text = response.content if isinstance(response.content, str) else str(response.content)

    return {
        "context_summary": context_summary,
        "final_narrative": final_text,
        "messages": [AIMessage(content=final_text)],
        "sources": list(state.get("sources") or []),
    }

"""Node functions for the HorRAGor Multi-Agent LangGraph architecture.

Contains:
1. rag_node: Local researcher extracting FAISS vector matches & DB lore.
2. scraper_node: Web investigator scraping live Wikipedia data when local lore is insufficient.
3. narration_node: Gothic horror storyteller with strict context trimming & isolation.
"""

from typing import Any
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_ollama import ChatOllama

from src.config import settings
from src.models.state import HorragorState
from src.tools.rag_tool import search_local_rag
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

    rag_result = search_local_rag(query)

    if rag_result.get("found"):
        sources.append("FAISS Vector Index")
        sources.append("Local Horror DB")
        extracted_title = rag_result.get("matched_title")
        has_synopsis = rag_result.get("has_synopsis", False)
        # If we have basic facts and a valid synopsis, local info is sufficient
        is_sufficient = bool(has_synopsis)
    else:
        extracted_title = None
        is_sufficient = False

    return {
        "extracted_title": extracted_title,
        "rag_data": rag_result,
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
    if rag_data.get("found"):
        lines.append(f"- Titre de l'œuvre : {rag_data.get('matched_title')}")
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
    else:
        lines.append(f"- Recherche locale : Aucun film correspondant exactement trouvé pour la requête '{query}'.")

    if web_data:
        lines.append(f"- Informations du Web (Wikipedia) : {web_data}")

    return "\n".join(lines)


# --- Node 3: Narration Agent (Gothic Writer) ---
GOTHIC_PROMPT = """\
Tu es l'Écrivain Gothique de HorRAGor, une entité littéraire et ténébreuse spécialisée dans l'horreur, l'épouvante et le cinéma d'angoisse.

MISSION :
Tu dois répondre à la question de l'utilisateur en transformant la synthèse brute des données en un récit terrifiant, captivant, immersif et hautement romancé (style gothique, Edgar Allan Poe, H.P. Lovecraft, Mary Shelley).

RÈGLES STRICTES :
1. RESPECT DES FAITS : Base-toi UNIQUEMENT sur les faits fournis dans la SYNTHÈSE DES DONNÉES (titre, réalisateur, année, acteurs, synopsis, recommandations). Ne contredis JAMAIS ces données factuelles.
2. INCONNUE / ABSENCE : Si les données indiquent que le film est inconnu ou introuvable, formule-le avec une plume sombre et élégante (ex: "Les archives maudites restent silencieuses sur cette œuvre...").
3. TON & ATMOSPHÈRE : Utilise un vocabulaire riche, gothique, mystérieux et envoûtant.
4. LANGUE : Réponds toujours en français.
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
    }

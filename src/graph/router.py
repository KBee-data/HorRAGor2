"""Routing functions for conditional edges in the HorRAGor StateGraph."""

from typing import Literal
from src.models.state import HorragorState


def route_after_rag(state: HorragorState) -> Literal["scraper_node", "narration_node"]:
    """Determines whether to trigger the Web Scraper or proceed straight to Narration.

    - If local FAISS & DB info is sufficient -> goes directly to 'narration_node'.
    - If local information is missing or incomplete -> routes to 'scraper_node'.
    """
    is_sufficient = state.get("is_local_info_sufficient", False)
    if is_sufficient:
        return "narration_node"
    return "scraper_node"

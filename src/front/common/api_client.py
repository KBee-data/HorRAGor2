"""Client HTTP du Front vers l'API (partage par tous les fronts).

POURQUOI un module dedie ET partage : c'est la seule "connaissance" commune a tout
front (l'URL de l'API + le format des messages). Si l'API change, on ne touche qu'ici,
et Streamlit comme un futur Gradio en beneficient. On reutilise les schemas Pydantic
du Back-End pour serialiser/valider -> Front et API parlent la meme structure.
"""

import httpx

from backend.config import settings
from backend.contracts.schemas import ChatRequest, ChatResponse


def send_message(message: str, session_id: str = "default") -> ChatResponse:
    """Envoie la question a POST /chat et renvoie la reponse validee."""
    req = ChatRequest(message=message, session_id=session_id)
    resp = httpx.post(
        f"{settings.api_base_url}/chat",
        json=req.model_dump(),
        timeout=60,  # large : un vrai agent (LLM + tools) peut etre lent
    )
    resp.raise_for_status()
    # Re-valide la reponse cote Front : on detecte tout ecart au contrat.
    return ChatResponse.model_validate(resp.json())

"""Routes de l'API.

Exigence du PDF : un endpoint UNIQUE `POST /chat` qui receptionne la question,
pilote l'agent jusqu'au verdict du Juge, et renvoie la reponse validee en JSON.
On ajoute `GET /health` (pratique pour la CI et le monitoring).

POURQUOI tout en `async` : aucune route ne doit bloquer la boucle d'evenements,
sinon le Front Streamlit gele en attendant la reponse.
"""

from typing import Annotated

from fastapi import APIRouter, Depends

from backend.api.deps import get_engine
from backend.contracts.interfaces import AgentEngine
from backend.contracts.schemas import ChatRequest, ChatResponse

router = APIRouter()

# Pattern `Annotated[..., Depends(...)]` recommande par FastAPI :
# declare la dependance une fois, reutilisable et compatible avec les linters
# (evite l'appel de fonction dans une valeur par defaut d'argument).
EngineDep = Annotated[AgentEngine, Depends(get_engine)]


@router.get("/health")
async def health() -> dict[str, str]:
    """Verifie que l'API repond (utilise par la CI et le Front)."""
    return {"status": "ok"}


@router.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest, engine: EngineDep) -> ChatResponse:
    """Delegue la question au moteur et renvoie la reponse validee."""
    return await engine.run(req)

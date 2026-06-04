"""Faux moteur : respecte le contrat AgentEngine, renvoie une reponse de test.

POURQUOI : decouple totalement l'API de l'agent. Tant que la signature
`run(req) -> ChatResponse` est respectee, l'API n'a pas besoin de savoir si
elle parle au mock ou au vrai graphe LangGraph. En temps 2, on remplace cette
classe par `backend.agent.graph.AgentGraph` sans rien changer cote API/Front.
"""

from backend.contracts.schemas import ChatRequest, ChatResponse
from backend.mocks.fixtures import FILMS


class FakeEngine:
    """Implementation factice de `backend.contracts.interfaces.AgentEngine`."""

    async def run(self, req: ChatRequest) -> ChatResponse:
        film = FILMS[0]
        return ChatResponse(
            answer=(
                f"(reponse de test) {film.title} a ete realise par "
                f"{film.director} en {film.release_year}."
            ),
            sources=["mock:fixtures"],
            verdict="mock",
        )

"""Boucle ReAct LangGraph (temps 2).

POURQUOI cette classe implemente `AgentEngine` : pour qu'au temps 2 on la branche
dans `backend.api.deps.get_engine` a la place du FakeEngine, SANS toucher a l'API.
Le contrat (`run(req) -> ChatResponse`) est identique : l'API ne voit pas la difference.

Flux cible : Agent (LLM) -> (Tools <-> Agent)* -> Juge -> reponse validee | fallback.
"""

from backend.contracts.schemas import ChatRequest, ChatResponse


class AgentGraph:
    """Implementation reelle de AgentEngine (a construire en temps 2)."""

    async def run(self, req: ChatRequest) -> ChatResponse:
        # TODO (temps 2) : compiler le graphe (Agent/Tools/Juge) et l'invoquer
        raise NotImplementedError

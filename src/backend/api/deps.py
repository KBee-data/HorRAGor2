"""Injection de dependances de l'API.

POURQUOI centraliser le choix du moteur ICI : c'est le SEUL endroit qui decide quelle
implementation d'`AgentEngine` tourne. Les routes recoivent l'abstraction et ignorent
le concret (inversion de dependance). Les tests surchargent `get_engine` (FakeEngine)
pour rester rapides et hors-ligne.
"""

from functools import lru_cache

from backend.agent.graph import AgentGraph
from backend.contracts.interfaces import AgentEngine


@lru_cache(maxsize=1)
def _engine() -> AgentGraph:
    # Construit une seule fois (compile le graphe LangGraph). Lazy : seulement au
    # premier /chat, pas a l'import.
    return AgentGraph()


def get_engine() -> AgentEngine:
    return _engine()

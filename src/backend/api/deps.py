"""Injection de dependances de l'API.

POURQUOI centraliser le choix du moteur ICI : c'est le SEUL endroit a changer pour
passer du mock au vrai agent. Les routes recoivent un `AgentEngine` abstrait et
ignorent quelle implementation concrete tourne derriere (inversion de dependance).
"""

from backend.contracts.interfaces import AgentEngine
from backend.mocks.fake_engine import FakeEngine


def get_engine() -> AgentEngine:
    # TODO (temps 2) : remplacer par le vrai moteur LangGraph, ex.
    #   from backend.agent.graph import AgentGraph
    #   return AgentGraph()
    return FakeEngine()

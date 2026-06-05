"""Etat partage circulant dans le graphe LangGraph.

POURQUOI ces champs :
- `messages` : l'historique (humain / IA / outils). Le reducer `add_messages` AJOUTE
  les nouveaux messages au lieu de remplacer la liste (essentiel pour la boucle ReAct).
- `retries` : nombre de corrections deja demandees par le Juge (boucle bornee).
"""

from typing import Annotated, TypedDict

from langgraph.graph.message import add_messages


class AgentState(TypedDict):
    messages: Annotated[list, add_messages]
    retries: int

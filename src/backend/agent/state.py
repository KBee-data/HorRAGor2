"""Etat partage circulant dans le graphe LangGraph (temps 2).

POURQUOI un TypedDict : LangGraph passe un dictionnaire d'etat de nœud en nœud.
Le typer documente les champs attendus (messages, observations des tools, verdict)
et aide l'editeur/le linter a reperer les erreurs.
"""

from typing import Annotated, TypedDict


class AgentState(TypedDict, total=False):
    # total=False : tous les champs sont optionnels (l'etat se remplit au fil du graphe).
    messages: Annotated[list, "historique de la conversation"]
    # TODO (temps 2) : observations des tools, reponse candidate, verdict du juge...

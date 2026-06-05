"""Exporte le graphe de l'agent en Mermaid (livrable du brief).

Lancement :
    uv run horragor-graph                       # affiche le Mermaid
    uv run horragor-graph > docs/graphe_agent_genere.mmd   # (re)genere le fichier

Le diagramme est genere a partir du graphe LangGraph compile : il reflete donc
TOUJOURS la structure reelle du code.
"""

from backend.agent.graph import build_graph


def main() -> None:
    print(build_graph().get_graph().draw_mermaid())


if __name__ == "__main__":
    main()

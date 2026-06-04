"""Brique agent (temps 2) — boucle ReAct LangGraph + nœud Juge deterministe.

POURQUOI LangGraph : modelise l'agent comme un graphe d'etats (Agent -> Tools ->
Juge), ce qui rend la boucle ReAct explicite, debogable et exportable en diagramme.
A terme, `AgentGraph` implementera `AgentEngine` et remplacera le FakeEngine.
"""

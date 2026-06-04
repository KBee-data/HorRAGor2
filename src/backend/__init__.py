"""Back-End HorRAGor2.

Regroupe TOUTE la logique metier (API, agent LangGraph, tools, acces donnees,
contrats, mocks, configuration). Le Front-End n'en consomme que les "contrats"
(schemas de donnees) et l'URL de l'API : aucune logique LLM/Supabase cote client.
"""

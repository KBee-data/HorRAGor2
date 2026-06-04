"""Boite a outils de l'agent (temps 2) — noms alignes sur le PDF.

POURQUOI des fonctions typees plutot qu'un acces libre a la base/au web :
le LLM choisit QUEL outil appeler, mais c'est notre code Python (sain et securise)
qui execute l'action. Le LLM ne genere jamais de SQL ni d'acces direct.

Outils :
- validate_film            : routeur FAISS (Nom -> ID), validation instantanee
- query_movie_metadata     : Tool 1 — metadonnees de base via SQL securise
- find_similar_horror_movies : Tool 2 — reco semantique via pgvector
- scrape_detailed_synopsis : Tool 3 — scraping Wikipedia a la demande
- calculate_movie_age      : Tool 4 — calcul d'age (Python natif, deterministe)
- horror_survival_simulator: Tool 5 (optionnel) — simulateur ludique
"""

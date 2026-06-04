"""Code Front-End reutilisable, AGNOSTIQUE de la techno d'affichage.

POURQUOI ce module : dialoguer avec l'API (HTTP + schemas du contrat) ne depend
pas du framework d'UI. En l'isolant ici, un futur front (Gradio, etc.) reutilise
exactement le meme client sans rien dupliquer.
"""

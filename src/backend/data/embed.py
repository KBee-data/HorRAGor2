"""Calcul des embeddings des films (pour la recherche vectorielle pgvector).

POURQUOI separer ce module : le modele d'embeddings (choix d'equipe via
settings.embedding_model) doit etre le MEME a l'ingestion et a la requete, sinon
les distances cosinus n'ont pas de sens. Un point unique evite les incoherences.
La dimension du vecteur doit correspondre a la colonne `vector(N)` de Supabase.
"""


def embed_texts(texts: list[str]) -> list[list[float]]:
    # TODO : appeler le modele d'embeddings choisi et renvoyer un vecteur par texte
    raise NotImplementedError

"""Construction de l'index FAISS des TITRES (memoire ephemere, en RAM).

Exigence du PDF : l'index ne contient QUE les couples [Nom du film : ID]. Il sert
de "routeur" ultra-rapide pour valider l'existence d'un film et recuperer son ID
AVANT toute action lourde (SQL, scraping...).

POURQUOI FAISS en RAM (et pas une requete SQL a chaque fois) : la validation
d'identifiant devient quasi instantanee et n'interroge pas la base principale.
La recherche semantique de CONTENU, elle, reste du ressort de pgvector (pas FAISS).
"""


def build_index() -> None:
    # TODO : encoder les titres, construire et sauvegarder l'index FAISS
    raise NotImplementedError

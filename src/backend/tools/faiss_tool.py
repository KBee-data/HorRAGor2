"""Routeur FAISS : validation instantanee de l'existence d'un film (par titre).

POURQUOI ce tool s'execute en premier : il confirme qu'un film existe et renvoie
son ID AVANT toute action couteuse (SQL, scraping). C'est le "routage rapide" du PDF.
"""

from backend.contracts.schemas import FilmRef


def validate_film(title: str) -> FilmRef | None:
    """Renvoie l'id du film si le titre existe dans l'index FAISS, sinon None."""
    # TODO (temps 2) : interroger l'index FAISS construit par la brique data
    raise NotImplementedError

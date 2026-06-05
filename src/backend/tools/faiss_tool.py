"""Routeur FAISS : validation instantanee de l'existence d'un film (par titre).

POURQUOI ce tool s'execute en premier : il confirme qu'un film existe et renvoie
son ID AVANT toute action couteuse (SQL, scraping). C'est le "routage rapide" du PDF.

Fonctionnement : on embedde le titre de la requete, on cherche le plus proche voisin
dans l'index, et on compare le score cosinus au seuil (settings.faiss_score_threshold).
Sous le seuil -> None (= film absent, l'agent enchaine sur "je ne sais pas" / Wikipedia).

L'index est un singleton de module : charge une fois (au demarrage de l'API, etape 5,
via set_index) ou paresseusement depuis le disque au premier appel.
"""

from backend.config import settings
from backend.contracts.schemas import FilmRef
from backend.data.embed import embed_text
from backend.data.faiss_index import TitleIndex, normalize_title

_index: TitleIndex | None = None


def set_index(index: TitleIndex) -> None:
    """Injecte l'index deja charge (appele au demarrage de l'API)."""
    global _index
    _index = index


def _get_index() -> TitleIndex:
    global _index
    if _index is None:
        # Repli : chargement paresseux depuis le disque si non injecte.
        _index = TitleIndex.load()
    return _index


def validate_film(title: str) -> FilmRef | None:
    """Renvoie l'id du film si le titre existe (score >= seuil), sinon None."""
    index = _get_index()
    vector = embed_text(normalize_title(title))
    results = index.search_vector(vector, k=1)
    if not results:
        return None
    score, film_id, matched_title = results[0]
    if score < settings.faiss_score_threshold:
        return None
    return FilmRef(id=film_id, title=matched_title)

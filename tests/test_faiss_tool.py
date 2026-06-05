"""Tests du tool validate_film — index injecte + embed_text moque (pas d'Ollama)."""

from backend.contracts.schemas import FilmRef
from backend.data.faiss_index import TitleIndex
from backend.tools import faiss_tool


def _toy_index() -> TitleIndex:
    vectors = [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0]]
    return TitleIndex.from_vectors(vectors, ids=[10, 20], titles=["The Thing", "Hereditary"])


def test_validate_film_match(monkeypatch):
    faiss_tool.set_index(_toy_index())
    # La requete "tombe" exactement sur le 1er vecteur -> score 1.0 >= seuil.
    monkeypatch.setattr(faiss_tool, "embed_text", lambda _t: [1.0, 0.0, 0.0])

    ref = faiss_tool.validate_film("The Thing")
    assert ref == FilmRef(id=10, title="The Thing")


def test_validate_film_below_threshold_returns_none(monkeypatch):
    faiss_tool.set_index(_toy_index())
    # Vecteur "entre" les deux -> cosinus ~0.707 < seuil 0.75 -> None.
    monkeypatch.setattr(faiss_tool, "embed_text", lambda _t: [1.0, 1.0, 0.0])

    assert faiss_tool.validate_film("titre inconnu") is None

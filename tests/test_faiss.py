"""Tests de l'index FAISS — vecteurs deterministes, AUCUN appel Ollama."""

from backend.data.faiss_index import TitleIndex, normalize_title


def test_normalize_title():
    assert normalize_title("  The Thing  ") == "the thing"


def _toy_index() -> TitleIndex:
    # 3 vecteurs orthogonaux -> chacun est son propre plus proche voisin.
    vectors = [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]]
    ids = [10, 20, 30]
    titles = ["The Thing", "Hereditary", "Alien"]
    return TitleIndex.from_vectors(vectors, ids, titles)


def test_search_returns_nearest():
    idx = _toy_index()
    score, film_id, title = idx.search_vector([1.0, 0.0, 0.0], k=1)[0]
    assert film_id == 10
    assert title == "The Thing"
    assert score > 0.99  # cosinus ~ 1 pour le vecteur identique


def test_search_distinguishes_vectors():
    idx = _toy_index()
    score, film_id, _ = idx.search_vector([0.0, 0.9, 0.1], k=1)[0]
    assert film_id == 20  # plus proche de [0,1,0]


def test_save_and_load_roundtrip(tmp_path):
    idx = _toy_index()
    idx.save(str(tmp_path))
    assert TitleIndex.exists(str(tmp_path))
    reloaded = TitleIndex.load(str(tmp_path))
    assert len(reloaded) == 3
    assert reloaded.search_vector([0.0, 0.0, 1.0], k=1)[0][1] == 30

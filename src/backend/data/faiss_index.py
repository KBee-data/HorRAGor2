"""Index FAISS des titres (routeur Nom -> ID).

Choix techniques :
- `IndexFlatIP` (produit scalaire) sur des vecteurs **L2-normalises** = similarite
  COSINUS exacte. Flat (force brute) suffit largement pour ~34k titres en RAM et
  evite tout reglage d'index approximatif.
- On garde un mapping `position -> (id, title)` aligne sur l'ordre d'ajout.
- Embedding des titres en **requetes concurrentes** (Ollama parallelise sur le GPU) :
  beaucoup plus rapide qu'un seul gros batch (cf. docs/faiss-pas-a-pas.md, etape 1).

La recherche (`search_vector`) ne fait PAS d'embedding : elle prend un vecteur deja
calcule. C'est le tool `validate_film` qui embeddera la requete. -> module testable
sans Ollama.
"""

import json
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import faiss
import numpy as np

from backend.config import _PROJECT_ROOT, settings
from backend.data.embed import embed_texts


def normalize_title(title: str) -> str:
    """Normalisation legere pour stabiliser le matching (casse/espaces)."""
    return title.strip().lower()


def _l2_normalize(mat: np.ndarray) -> np.ndarray:
    norms = np.linalg.norm(mat, axis=1, keepdims=True)
    norms[norms == 0] = 1.0  # evite la division par zero
    return mat / norms


def _resolve_dir(index_dir: str | None) -> Path:
    raw = index_dir or settings.faiss_index_dir
    p = Path(raw)
    return p if p.is_absolute() else (_PROJECT_ROOT / p)


def _embed_concurrent(texts, embed_fn, workers, chunk_size):
    """Embedde `texts` via plusieurs requetes paralleles (ordre preserve)."""
    chunks = [texts[i : i + chunk_size] for i in range(0, len(texts), chunk_size)]
    vectors: list[list[float]] = []
    with ThreadPoolExecutor(max_workers=workers) as ex:
        for chunk_vecs in ex.map(embed_fn, chunks):  # map preserve l'ordre
            vectors.extend(chunk_vecs)
    return vectors


class TitleIndex:
    """Index FAISS des titres + mapping vers (id, title)."""

    INDEX_FILE = "titles.index"
    MAP_FILE = "titles_map.json"

    def __init__(self, index: faiss.Index, ids: list[int], titles: list[str]):
        self.index = index
        self.ids = ids
        self.titles = titles

    # --- Construction ---------------------------------------------------------
    @classmethod
    def from_vectors(cls, vectors, ids, titles) -> "TitleIndex":
        mat = _l2_normalize(np.asarray(vectors, dtype="float32"))
        index = faiss.IndexFlatIP(mat.shape[1])
        index.add(mat)
        return cls(index, list(ids), list(titles))

    @classmethod
    def build_from_pairs(cls, pairs, embed_fn=embed_texts, workers=10, chunk_size=32):
        """Construit l'index a partir de couples (id, title)."""
        ids = [int(i) for i, _ in pairs]
        titles = [str(t) for _, t in pairs]
        normalized = [normalize_title(t) for t in titles]
        vectors = _embed_concurrent(normalized, embed_fn, workers, chunk_size)
        return cls.from_vectors(vectors, ids, titles)

    # --- Recherche ------------------------------------------------------------
    def search_vector(self, vector, k: int = 1) -> list[tuple[float, int, str]]:
        """Renvoie [(score_cosinus, id, title)] des k plus proches (vecteur deja calcule)."""
        q = _l2_normalize(np.asarray([vector], dtype="float32"))
        scores, idx = self.index.search(q, k)
        results = []
        for score, pos in zip(scores[0], idx[0], strict=True):
            if pos == -1:  # FAISS renvoie -1 si moins de k voisins
                continue
            results.append((float(score), self.ids[pos], self.titles[pos]))
        return results

    def __len__(self) -> int:
        return self.index.ntotal

    # --- Persistance ----------------------------------------------------------
    def save(self, index_dir: str | None = None) -> Path:
        d = _resolve_dir(index_dir)
        d.mkdir(parents=True, exist_ok=True)
        faiss.write_index(self.index, str(d / self.INDEX_FILE))
        (d / self.MAP_FILE).write_text(
            json.dumps({"ids": self.ids, "titles": self.titles}), encoding="utf-8"
        )
        return d

    @classmethod
    def load(cls, index_dir: str | None = None) -> "TitleIndex":
        d = _resolve_dir(index_dir)
        index = faiss.read_index(str(d / cls.INDEX_FILE))
        data = json.loads((d / cls.MAP_FILE).read_text(encoding="utf-8"))
        return cls(index, data["ids"], data["titles"])

    @classmethod
    def exists(cls, index_dir: str | None = None) -> bool:
        d = _resolve_dir(index_dir)
        return (d / cls.INDEX_FILE).exists() and (d / cls.MAP_FILE).exists()

"""Construction de l'index FAISS des titres (job offline).

Lancement :
    uv run horragor-faiss            # build complet
    uv run horragor-faiss --limit 500   # sous-ensemble (validation rapide)

Etapes : load_titles() -> embeddings concurrents -> IndexFlatIP -> persistance disque.
On persiste l'index (faiss_index/) pour le recharger instantanement au demarrage de
l'API, sans re-embedder a chaque fois.
"""

import argparse
import time

from backend.data.faiss_index import TitleIndex
from backend.data.titles import load_titles


def build(limit: int | None = None) -> None:
    """Construit et persiste l'index FAISS des titres (reutilisable, sans argparse)."""
    pairs = load_titles()
    if limit:
        pairs = pairs[:limit]

    print(f"{len(pairs)} titres a embedder...")
    t0 = time.perf_counter()
    index = TitleIndex.build_from_pairs(pairs)
    out = index.save()
    dt = time.perf_counter() - t0
    print(f"✅ Index construit ({len(index)} titres) en {dt:.1f}s -> {out}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Construit l'index FAISS des titres.")
    parser.add_argument("--limit", type=int, default=None, help="limiter le nombre de titres")
    args = parser.parse_args()
    build(args.limit)


if __name__ == "__main__":
    main()

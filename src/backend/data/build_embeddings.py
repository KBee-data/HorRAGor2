"""Genere les embeddings de synopsis et les insere dans movie_embeddings (pgvector).

Lancement :
    uv run horragor-embeddings --limit 500   # valider sur un sous-ensemble
    uv run horragor-embeddings               # tout le catalogue (films avec synopsis)

Etapes : lire (id, overview) -> embeddings concurrents (Ollama) -> upsert.
Le vecteur est passe en litteral SQL caste en `vector` (pas d'adaptateur a configurer).
"""

import argparse
import time

from sqlalchemy import text

from backend.data.db import get_engine
from backend.data.embed import embed_texts_concurrent


def _load_overviews(limit: int | None) -> list[tuple[int, str]]:
    sql = (
        "select id, overview from movies "
        "where overview is not null and overview <> '' order by id"
    )
    if limit:
        sql += f" limit {int(limit)}"
    with get_engine().connect() as conn:
        return [(r[0], r[1]) for r in conn.execute(text(sql)).all()]


def _vec_literal(vector: list[float]) -> str:
    """Format pgvector : '[v1,v2,...]'."""
    return "[" + ",".join(f"{x:.6f}" for x in vector) + "]"


_UPSERT = text(
    "insert into movie_embeddings (movie_id, embedding) "
    "values (:id, cast(:emb as vector)) "
    "on conflict (movie_id) do update set embedding = excluded.embedding"
)


def build(limit: int | None = None, batch: int = 500) -> None:
    """Genere et upsert les embeddings de synopsis + index HNSW (reutilisable, sans argparse)."""
    rows = _load_overviews(limit)
    print(f"{len(rows)} synopsis a embedder...")
    t0 = time.perf_counter()

    vectors = embed_texts_concurrent([overview for _, overview in rows])

    inserted = 0
    engine = get_engine()
    for start in range(0, len(rows), batch):
        chunk = rows[start : start + batch]
        chunk_vecs = vectors[start : start + batch]
        # executemany (liste de params) -> psycopg groupe les inserts (bien plus rapide
        # qu'un round-trip reseau par ligne).
        params = [
            {"id": movie_id, "emb": _vec_literal(vector)}
            for (movie_id, _), vector in zip(chunk, chunk_vecs, strict=True)
        ]
        with engine.begin() as conn:
            conn.execute(_UPSERT, params)
        inserted += len(chunk)

    # Index ANN cosinus (HNSW) pour une recherche rapide. Idempotent.
    with engine.begin() as conn:
        conn.execute(
            text(
                "create index if not exists movie_embeddings_hnsw "
                "on movie_embeddings using hnsw (embedding vector_cosine_ops)"
            )
        )

    dt = time.perf_counter() - t0
    print(f"✅ {inserted} embeddings inseres (+ index HNSW) en {dt:.1f}s.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Construit les embeddings de synopsis.")
    parser.add_argument("--limit", type=int, default=None, help="limiter le nombre de films")
    parser.add_argument("--batch", type=int, default=500, help="taille des lots d'insertion")
    args = parser.parse_args()
    build(args.limit, args.batch)


if __name__ == "__main__":
    main()

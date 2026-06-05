"""Active l'extension pgvector et cree la table movie_embeddings (idempotent).

Lancement : uv run horragor-pgvector-setup

N'ajoute qu'une table dediee (movie_embeddings) — ne modifie pas la table movies de
Part 1. Si `create extension` echoue (droits insuffisants), activer l'extension
"vector" depuis le dashboard Supabase (Database > Extensions) puis relancer.
"""

from sqlalchemy import text

from backend.config import settings
from backend.data.db import get_engine

_DDL = [
    "create extension if not exists vector",
    (
        "create table if not exists movie_embeddings ("
        " movie_id bigint primary key references movies(id) on delete cascade,"
        f" embedding vector({settings.embedding_dim})"
        ")"
    ),
]


def main() -> None:
    with get_engine().begin() as conn:
        for stmt in _DDL:
            conn.execute(text(stmt))
            print("OK :", stmt.split("(")[0].strip())
    print(f"✅ pgvector pret (table movie_embeddings, vector({settings.embedding_dim})).")


if __name__ == "__main__":
    main()

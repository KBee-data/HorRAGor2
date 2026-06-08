"""Reinitialise les artefacts de donnees de Part 2 apres un rechargement de la base.

POURQUOI : Part 2 ne charge pas la base, elle construit DEUX artefacts indexes sur
`movies.id` : l'index FAISS des titres et la table pgvector `movie_embeddings`. Quand la
Partie 1 recharge la base, les `id` (auto-increment) changent -> il faut tout reconstruire
depuis Supabase, sinon les ids ne correspondent plus (mauvais film renvoye).

Enchaine : index FAISS -> schema pgvector -> vidage de movie_embeddings -> embeddings.

Lancement (APRES que la Partie 1 a recharge la base) :
    uv run horragor-reset-data
"""

from sqlalchemy import text

from backend.data import build_embeddings, build_faiss, setup_pgvector
from backend.data.db import get_engine


def main() -> None:
    print("=== Reinitialisation des donnees Part 2 (tout depuis Supabase) ===")

    print("\n[1/4] Reconstruction de l'index FAISS des titres...")
    build_faiss.build()

    print("\n[2/4] Extension pgvector + table movie_embeddings...")
    setup_pgvector.main()

    print("\n[3/4] Vidage des anciens embeddings (ids perimes)...")
    with get_engine().begin() as conn:
        conn.execute(text("truncate table movie_embeddings"))
    print("  movie_embeddings videe.")

    print("\n[4/4] Generation des embeddings de synopsis...")
    build_embeddings.build()

    print("\n✅ Reinitialisation terminee. Redemarre l'API : uv run horragor-api")


if __name__ == "__main__":
    main()

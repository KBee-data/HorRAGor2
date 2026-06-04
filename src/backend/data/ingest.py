"""Ingestion du golden data dans Supabase.

Lancement :
    uv run horragor-ingest

Etapes (a completer par C, a reception du golden data) :
  1. lire le golden data (CSV/JSON issu de la Partie 1) ;
  2. creer / peupler la table films (via le connecteur securise) ;
  3. declencher embed.py (vecteurs pgvector) puis build_faiss.py (index titres).

POURQUOI une fonction `main()` dediee : sert de point d'entree au script
`horragor-ingest` defini dans pyproject.toml (lancement reproductible).
"""


def main() -> None:
    # TODO : implementer l'ingestion
    print("Ingestion : a implementer (en attente du golden data).")


if __name__ == "__main__":
    main()

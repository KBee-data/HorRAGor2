# Reco pgvector — journal pas à pas

Tool 2 du brief : `find_similar_horror_movies` — recommander des films sémantiquement proches
par **similarité cosinus** sur les **vecteurs de synopsis**, via **pgvector** (Supabase).

Constat amont : Part 1 n'a pas créé de vecteurs → Part 2 les **génère** (embeddings `overview`
avec `nomic-embed-text`, 768). Stockage : **table dédiée `movie_embeddings`**. On valide sur un
**sous-ensemble** avant le full. Branche `feat/pgvector-reco`, un commit par étape.

---

## Étape 1 — Schéma : extension + table

**But :** préparer le stockage vectoriel sans toucher au schéma hérité de Part 1.

**Ce que je fais :**
- `src/backend/data/setup_pgvector.py` (CLI `horragor-pgvector-setup`), idempotent :
  - `create extension if not exists vector` ;
  - `create table if not exists movie_embeddings (movie_id bigint PK → movies(id),
    embedding vector(768))`.

**Pourquoi une table dédiée :** isole les vecteurs, n'altère pas `movies` ni les autres tables
de l'instance partagée. FK + `on delete cascade` = cohérence avec le catalogue.

**Vérifié (Supabase réel) :** `pgvector: True`, `table movie_embeddings: True`.

**Vérifier :** `uv run horragor-pgvector-setup` (ré-exécutable sans risque).

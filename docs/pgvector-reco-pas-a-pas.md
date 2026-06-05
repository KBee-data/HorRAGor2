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

---

## Étape 2 — Génération + insertion des embeddings

**But :** vectoriser les synopsis et les stocker dans `movie_embeddings`.

**Ce que je fais :**
- Refactor DRY : `embed.embed_texts_concurrent(texts)` (extrait de `faiss_index.py`) — réutilisé
  par le build FAISS (titres) et ce build (synopsis).
- `src/backend/data/build_embeddings.py` (CLI `horragor-embeddings [--limit N]`) :
  lit `(id, overview)` (synopsis non vide) → embeddings concurrents → **upsert** dans
  `movie_embeddings` (le vecteur est passé en littéral SQL casté en `vector`).
- **Insert en `executemany`** (psycopg groupe les requêtes) + création de l'index **HNSW**
  cosinus (`vector_cosine_ops`) en fin de build (idempotent).

**Mesures (sous-ensemble de 500) :**
- Insert ligne par ligne : **96 s** (le réseau dominait).
- `executemany` : **~5-6 s** → extrapolation full 31 284 ≈ **~1 min**.

**Vérifié :** 500 vecteurs en base, `dim = 768`, index `movie_embeddings_hnsw` présent.

**Build complet :** `uv run horragor-embeddings` (job ponctuel, ~1 min). Le sous-ensemble de 500
suffit pour développer/tester l'étape 3.

**Vérifier :** `uv run horragor-embeddings --limit 500`.

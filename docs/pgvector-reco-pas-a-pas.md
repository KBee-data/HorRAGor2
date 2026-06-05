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
- `executemany` : **~5-6 s** (le coût restant est l'embedding des synopsis, plus longs que les titres).

**Vérifié :** 500 vecteurs en base, `dim = 768`, index `movie_embeddings_hnsw` présent.

**Build complet (réalisé) :** `uv run horragor-embeddings` → **31 284 embeddings en 352 s (~5,9 min)**,
soit 100 % des films ayant un synopsis. Job ponctuel.

**Vérifier :** `uv run horragor-embeddings --limit 500`.

---

## Étape 3 — `recommend_similar` (repository)

**But :** la recherche de similarité cosinus elle-même.

**Ce que je fais :**
- `repository.SupabaseFilmRepository.recommend_similar(film_id, k=5)` :
  `... order by e.embedding <=> (select embedding from movie_embeddings where movie_id = :id) limit :k`
  — le vecteur de la graine reste **dans la base** (sous-requête) → aucun transfert ni
  adaptateur Python à configurer. Exclut le film lui-même ; renvoie `[]` si pas d'embedding.

**Pourquoi la sous-requête :** plus simple et robuste qu'un binding de vecteur côté Python ;
l'index HNSW accélère le `<=>`.

**Vérifié (sous-ensemble) :** graine « Send Help » → *Predator Island, Blood House,
Satan's Triangle, Man Eaters, Scarce* (horreur/survie cohérents) ; film sans embedding → `[]`.

**Vérifier :** test d'intégration (cf. étape 4) ou appel direct `recommend_similar(id)`.

---

## Étape 4 — Tool `find_similar_horror_movies`

**But :** exposer la reco sous la forme appelée par l'agent.

**Ce que je fais :**
- `tools/pgvector_tool.py` : `find_similar_horror_movies(film_id, k=5)` délègue au repository
  (singleton injectable, comme `sql_tool`).
- `tests/test_pgvector_tool.py` : unitaire avec **repository factice** (CI-safe) + test
  d'**intégration** réel `skipif` sans `DATABASE_URL`.

**Vérifié :** 27 tests verts (intégration incluse).

---

## Récapitulatif

Reco pgvector complète (branche `feat/pgvector-reco`) : extension + table `movie_embeddings`
→ génération des embeddings de synopsis → `recommend_similar` (cosinus `<=>`, index HNSW) →
tool `find_similar_horror_movies`.

**Build complet réalisé** : 31 284 films vectorisés (100 % de ceux ayant un synopsis).
Plus aucun bloqueur côté brique data : tous les tools data sont prêts (`validate_film`,
`query_movie_metadata`, `find_similar_horror_movies`, `calculate_movie_age`).

**Démo (catalogue complet)** — la chaîne `validate_film → find_similar_horror_movies` :
```
Alien      -> The X from Outer Space, Queen of Blood, Alien Escape   (Horror/Sci-Fi)
The Thing  -> Creature, The Brain Eaters, The Thing (2011)           (créature/body-horror)
Hereditary -> Satan's Slaves, The Inheritance, The Heiress           (héritage/occulte)
```

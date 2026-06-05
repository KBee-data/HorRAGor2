# Connecteur SQL — journal pas à pas

Implémentation du **connecteur SQL sécurisé** (brique C) : des fonctions Python typées
au-dessus de la base Supabase, pour que l'agent obtienne les métadonnées d'un film **sans
jamais générer de SQL**. Branche `feat/sql-connector`, un commit par étape.

Décisions amont : connexion **SQLAlchemy + `DATABASE_URL`** (`docs/connexion-supabase.md`) ;
réalisateur/casting **enrichis via TMDB** (absents de la base).

---

## Étape 1 — Engine + `get_metadata` (jointures)

**But :** lire les métadonnées réelles d'un film (table `movies` + jointures).

**Ce que je fais :**
- Dépendances : `uv add sqlalchemy "psycopg[binary]"` (la variante *binary* embarque `libpq`).
- `src/backend/data/db.py` : `get_engine()` — engine SQLAlchemy unique (caché, `pool_pre_ping`)
  construit depuis `settings.database_url`.
- `src/backend/data/repository.py` : `SupabaseFilmRepository.get_metadata(id)` →
  requêtes **paramétrées** sur `movies` + jointure `movie_genres`/`genres` + table `ratings`,
  mappées vers `FilmMetadata` (année ← `release_date`, genres ← jointure, note ← imdb/tmdb,
  synopsis ← `overview`).
- **Contrat** : `FilmMetadata.genre` (str) → **`genres` (list[str])** — un film a plusieurs
  genres (aligné sur la réalité de la base). Fixtures du mock mises à jour.
- `tests/test_repository.py` : sur un **SQLite local** (même schéma, CI-safe), vérifie le
  mapping des jointures et le cas « film absent ».

**Pourquoi ces choix :**
- *Engine injectable* (`engine=None` → Supabase ; injecté → SQLite en test) : testable sans réseau.
- *Requêtes paramétrées* : zéro injection, et le LLM n'écrit jamais de SQL (exigence brief).
- *imdb prioritaire pour `rating`* : échelle 0-10 cohérente (Rotten Tomatoes est en 0-100).

**Preuve (Supabase réel, id 41 = Hereditary) :**
```
release_year=2018 | genres=['Drama','Horror','Mystery','Mystery & Thriller','Thriller']
rating=7.3 (imdb) | synopsis="When Ellen, the matriarch..." | director=None cast=[] (TMDB ensuite)
```

**Vérifier :** `uv run pytest -q tests/test_repository.py`.

---

## Étape 2 — Tool `query_movie_metadata`

**But :** exposer le connecteur sous la forme appelée par l'agent.

**Ce que je fais :**
- `src/backend/tools/sql_tool.py` : `query_movie_metadata(film_id) -> FilmMetadata | None`
  délègue au `SupabaseFilmRepository` (singleton injectable via `set_repository`).
- `tests/test_sql_tool.py` : repository **factice** injecté (pas de base réelle).

**⚠️ Constat critique (cohérence des `id`) :**
Test réel : `query_movie_metadata(6050)` renvoie « Penumbra » côté Supabase, alors que l'index
FAISS (bâti sur le **SQLite local**) associe id 6050 à « The Thing ». Les `id` **diffèrent**
entre SQLite et Supabase (ex. « The Thing » = id 2457 sur Supabase, 6050 en local).

→ La chaîne `validate_film (FAISS) → id → query_movie_metadata (SQL)` renverrait le **mauvais
film**. **Correctif obligatoire** : reconstruire l'index FAISS depuis **Supabase** (même source
que les métadonnées) pour que les `id` soient cohérents. C'est l'étape suivante.

**Vérifier :** `uv run pytest -q tests/test_sql_tool.py`.

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

---

## Étape 3 — Bascule de la source FAISS vers Supabase (cohérence des ids)

**But :** corriger l'incohérence des `id` détectée à l'étape 2 — l'index FAISS doit utiliser
les `id` de **Supabase** (mêmes que le connecteur SQL).

**Ce que je fais :**
- `src/backend/data/titles.py` — `load_titles()` choisit sa source dans cet ordre :
  1. `db_path` explicite → SQLite (override tests / dev hors-ligne) ;
  2. `settings.database_url` défini → **Supabase** (source de vérité des ids) ;
  3. sinon → SQLite local (repli).
- Reconstruction de l'index : `uv run horragor-faiss` lit désormais Supabase
  (**33 961 titres en ~98 s**).

**Pourquoi :** l'`id` renvoyé par `validate_film` sert de clé à `query_movie_metadata`. Les deux
doivent provenir de la même base, sinon on mélange les films.

**Preuve (chaîne complète FAISS → SQL) :**
```
'The Thing' -> FAISS id=2457 -> SQL: The Thing 1982, note 8.2          ✅
'Hereditary'-> FAISS id=41   -> SQL: Hereditary 2018, note 7.3         ✅
'Alien'     -> FAISS id=31   -> SQL: Alien 1979, note 8.5              ✅
```

**Vérifier :** `uv run pytest -q` (tests SQLite inchangés) puis le test de chaîne ci-dessus.

---

## Étape 4 — Enrichissement TMDB (réalisateur + casting)

**But :** ajouter réalisateur et casting, absents de la base, via l'API TMDB (chaque film a
son `tmdb_id`).

**Ce que je fais :**
- `config.py` : `tmdb_token` (secret, Bearer v4) + `tmdb_base_url` ; `.env.example` documenté.
- Contrat : `FilmMetadata.tmdb_id` ajouté ; `repository.get_metadata` le sélectionne.
- `src/backend/data/tmdb.py` : `get_credits(tmdb_id)` → `{director, cast}` (Bearer, comme Part 1).
- `tools/sql_tool.py` : `query_movie_metadata` enrichit director/cast via TMDB **si** un token
  est configuré et que le film a un `tmdb_id`. **Best-effort** : un échec réseau n'empêche pas
  la réponse (les faits issus de la base restent intacts).
- Tests : client TMDB **mocké** ; enrichissement du tool **mocké** ; cas « sans tmdb_id » =
  aucun appel réseau.

**Pourquoi best-effort :** la fidélité des données de la base (0 % hallucination) ne doit jamais
dépendre de la disponibilité d'une API externe.

**Preuve (chaîne réelle FAISS → SQL → TMDB) :**
```
The Thing (1982)  -> réal. John Carpenter | casting Kurt Russell, Wilford Brimley, T.K. Carter
Hereditary (2018) -> réal. Ari Aster      | casting Toni Collette, Alex Wolff, Gabriel Byrne
```

**Vérifier :** `uv run pytest -q tests/test_tmdb.py tests/test_sql_tool.py`.

---

## Récapitulatif

Connecteur SQL complet (branche `feat/sql-connector`) : `get_metadata` (SQLAlchemy) →
`query_movie_metadata` (tool) → cohérence des ids FAISS/Supabase → enrichissement TMDB.
La chaîne **`validate_film` → `query_movie_metadata`** renvoie des métadonnées fidèles et
complètes (année, genres, note, synopsis, réalisateur, casting).

**Suite (réalisée) :** la reco **pgvector** (`find_similar_horror_movies`) —
voir [`pgvector-reco-pas-a-pas.md`](pgvector-reco-pas-a-pas.md).

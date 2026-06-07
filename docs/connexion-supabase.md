# Décision — Connexion à la base Supabase

> Statut : **tranché**. Accès à la base via **SQLAlchemy + `DATABASE_URL`** (connexion
> PostgreSQL/psycopg), et non via le SDK REST `supabase-py`.

## Contexte

La base (films d'horreur) est hébergée sur **Supabase** = un PostgreSQL managé. La Partie 1
l'a créée avec des **modèles ORM SQLAlchemy** (tables `movies`, `genres`, `movie_genres`,
`ratings`, `movie_keywords`, `sources_metadata`). En Partie 2, le Back-End doit lire ces
données (métadonnées, reco pgvector) via des **fonctions Python typées** (les tools), le LLM
ne générant jamais de SQL.

Deux façons d'accéder à Supabase :
- **A. SQLAlchemy + `DATABASE_URL`** : connexion PostgreSQL native via une *connection string*
  (`postgresql+psycopg://user:mdp@host:5432/postgres`). SQL/ORM complet (jointures, agrégats,
  opérateur pgvector `<=>`).
- **B. SDK `supabase-py`** : client de l'API REST auto-générée (PostgREST), avec `SUPABASE_URL`
  + `SUPABASE_KEY`. Pratique pour CRUD simple, Auth, Storage, Realtime, RLS ; jointures
  complexes et pgvector → via fonctions RPC (laborieux).

## Ce que disent les briefs

**Partie 1** (section « Modélisation et Persistance des Données (Supabase & SQLAlchemy) ») —
mandat explicite :
> « Vous utiliserez **SQLAlchemy ORM** pour assurer l'interface entre votre code et le moteur
> de stockage. […] votre base de données sera déployée et hébergée sur **Supabase**. »

**Partie 2** (critère « Encapsulation des accès Supabase ») — l'objectif est la **sécurité**,
pas une techno imposée :
> « toutes les clés d'API et l'initialisation du client […] devront être **confinées au sein du
> Back-End**. […] Aucune communication directe avec la base depuis l'interface client. »

Le mot « SDK » y est un raccourci : se connecter au **Postgres** de Supabase via une connection
string **est** un accès officiel à Supabase.

## Décision et justification

**On retient A — SQLAlchemy + `DATABASE_URL`.**

1. **Continuité Partie 1** : le brief P1 impose SQLAlchemy, et la base existe déjà sous cette
   forme → on réutilise directement les modèles ORM et les jointures.
2. **Nature des données** : schéma relationnel (genres en N-N, notes multi-sources) + reco
   **pgvector** → du SQL relationnel, naturel en SQLAlchemy, pénible via le SDK REST.
3. **Sécurité respectée à l'identique** : la `DATABASE_URL` (avec mot de passe) vit dans le
   `.env` du Back-End ; le Front ne parle qu'à l'API. L'exigence P2 ne dépend pas du choix
   SDK vs SQLAlchemy.

`SUPABASE_URL`/`SUPABASE_KEY` restent disponibles (optionnels) pour un éventuel usage
REST/Storage/Auth, mais ne sont **pas** l'accès principal à la base.

## Ce qui est figé maintenant (cette branche)

- `config.py` : ajout de `database_url` (secret, défaut vide, confiné Back-End).
- `.env.example` : `DATABASE_URL` documenté (format psycopg) dans la section SECRETS.
- Décision tracée ici, dans `docs/architecture.md` (§ Décisions) et en mémoire projet.

## Étapes d'implémentation (réalisées)

1. **Dépendances** : `uv add sqlalchemy "psycopg[binary]"` (la variante *binary* embarque `libpq`).
2. **Engine partagé** : un module `backend/data/db.py` qui crée l'`engine`/`Session`
   SQLAlchemy à partir de `settings.database_url` (cf. pattern de Part 1 : `pool_pre_ping=True`).
   Possibilité de **réutiliser les modèles ORM** de Part 1 (les recopier dans `data/models.py`,
   lecture seule, plutôt qu'une dépendance inter-dépôts).
3. **`SupabaseFilmRepository`** (implémente `contracts.interfaces.FilmRepository`) :
   - `get_metadata(id)` : `movies` + jointures `genres` et `ratings` → `FilmMetadata`
     (année ← `release_date`, genre ← jointure, note ← `ratings`, synopsis ← `overview`).
   - `recommend_similar(id, k)` : recherche pgvector (`embedding <=> :q`) — nécessite la
     décision « stockage des embeddings » (table dédiée vs colonne) + génération des vecteurs.
   - `validate_film(title)` : déléguée au routeur FAISS existant.
4. **Bascule de la source FAISS** : `data/titles.load_titles()` lira `movies` via SQLAlchemy
   quand `DATABASE_URL` est défini (sinon repli sur le SQLite local de dev).
5. **Tools** : `query_movie_metadata` et `find_similar_horror_movies` appellent le repository.

> Décisions liées, depuis tranchées : **stockage des embeddings** = table dédiée
> `movie_embeddings` (cf. `pgvector-reco-pas-a-pas.md`) ; **réalisateur/casting** = enrichis
> via **TMDB**.

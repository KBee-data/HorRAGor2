# HorRAGor2 — L'Agent de l'Horreur 👻

Agent conversationnel **RAG** (LangGraph, boucle **ReAct** + **Juge** anti-hallucination) sur une
base de **films d'horreur**, exposé via une **API FastAPI** asynchrone et une **interface de chat
Streamlit**. 100 % local (Ollama) — aucune clé API requise pour l'IA.

Stack : LangGraph · Ollama (LLM + Juge + embeddings, local) · FAISS · Supabase (SQL + pgvector)
· TMDB · FastAPI · Streamlit · uv.

## Prérequis

- [uv](https://docs.astral.sh/uv/) et [Ollama](https://ollama.com) installés.
- Modèles Ollama :
  ```bash
  ollama pull qwen2.5:7b       # agent (ReAct) + juge (anti-hallucination)
  ollama pull nomic-embed-text # embeddings (768 dim)
  ```
- Une base **Supabase** (PostgreSQL) accessible — schéma issu de la Partie 1.

## Installation & configuration

```bash
uv sync --extra dev
cp .env.example .env
```

À renseigner dans `.env` :
- `DATABASE_URL` — connexion Supabase (`postgresql+psycopg://…`), **requise**.
- `TMDB_TOKEN` — token v4 TMDB, **optionnel** (enrichit réalisateur + casting).

## Préparation des données (une fois)

```bash
uv run horragor-faiss            # index FAISS des titres (routeur de validation)
uv run horragor-pgvector-setup   # active pgvector + crée la table movie_embeddings
uv run horragor-embeddings       # vectorise les synopsis (recommandation)
```

## Lancer l'application

```bash
# Terminal 1 — API (agent)
uv run horragor-api

# Terminal 2 — interface (DEPUIS LA RACINE, pour le thème sombre .streamlit/config.toml)
uv run streamlit run src/front/streamlit/app.py   # -> http://localhost:8501
```

## Qualité

```bash
uv run ruff check .
uv run pytest -q
```

## Commandes disponibles

| Commande | Rôle |
|---|---|
| `uv run horragor-api` | Lance l'API FastAPI (`/health`, `/chat`) |
| `uv run horragor-faiss` | Construit l'index FAISS des titres |
| `uv run horragor-search "titre"` | Teste / calibre la recherche FAISS |
| `uv run horragor-pgvector-setup` | Active pgvector + table d'embeddings |
| `uv run horragor-embeddings` | Génère les embeddings de synopsis |
| `uv run horragor-graph` | Exporte le schéma du graphe (Mermaid) |
| `uv run horragor-trace` | Affiche la trace du dernier run (lisible) ; `-n N` pour les N derniers |

## Trace du raisonnement (logs)

Chaque requête `/chat` produit une **trace fine** de tout le parcours interne (outil →
embedding → FAISS → SQL → TMDB → pgvector → Wikipédia → juge → verdict). On peut la lire :

- **dans l'app** : l'expander « 🔍 Raisonnement » sous chaque réponse ;
- **en terminal** : `uv run horragor-trace` (relit le dernier run de façon lisible) ;
- **données brutes** : `logs/traces.jsonl` (une ligne JSON par run).

> Le dossier **`logs/` est gitignoré** : les traces sont des artefacts d'exécution, jamais
> versionnés. Le *code* de tracing vit dans `src/backend/trace.py` (collecteur via `contextvars`).

## Structure

Deux packages sous `src/` : **`front`** (interface) et **`backend`** (toute la logique métier).

```
src/
├── front/                 Front-End (organisé par techno)
│   ├── common/            ·   client HTTP partagé (réutilisable par un futur Gradio)
│   └── streamlit/         ·   front Streamlit (app.py)
└── backend/
    ├── config.py          réglages centraux (.env)
    ├── contracts/         schémas Pydantic + interfaces (le « langage commun »)
    ├── mocks/             faux moteur + fixtures (tests / dév sans IA)
    ├── api/               FastAPI async (/health, /chat)
    ├── data/              Supabase (SQL + pgvector), index FAISS, TMDB
    ├── tools/             fonctions data typées (FAISS, SQL, pgvector, Wikipédia, âge)
    └── agent/             boucle ReAct LangGraph + Juge
```

Le **Front** ne contient aucune logique métier : il appelle l'API en HTTP et réutilise les
`contracts` du Back-End comme unique source de vérité sur la forme des données (« découplage
strict »). Toutes les clés / accès Supabase sont **confinés au Back-End**.

### Les outils de l'agent

L'agent expose au LLM des outils **par titre** (`lookup_movie`, `find_similar`, `movie_age`,
`wikipedia_synopsis`, dans `agent/tools_registry.py`) qui composent les fonctions data :

| Fonction | Fichier | Rôle |
|---|---|---|
| `validate_film` | `tools/faiss_tool.py` | Routeur FAISS : valide un titre → `id` |
| `query_movie_metadata` | `tools/sql_tool.py` | Métadonnées (année, genres, note, synopsis) + TMDB |
| `find_similar_horror_movies` | `tools/pgvector_tool.py` | Reco sémantique (pgvector, cosinus) |
| `scrape_detailed_synopsis` | `tools/wikipedia_tool.py` | Synopsis Wikipédia à la demande |
| `calculate_movie_age` | `tools/temporal_tool.py` | Âge du film (Python natif) |

## Workflow Git

Branches `feat/<brique>-<sujet>` → Pull Request → review → merge sur `main`.
On ne modifie pas `backend/contracts/` sans prévenir l'équipe.

> Dépôt public : aucun secret ne doit être commité. Les clés vivent dans `.env`
> (ignoré par git) ; seul `.env.example`, sans valeurs, est versionné.

## Documentation

Architecture, schéma du graphe et **journaux de développement** (FAISS, connecteur SQL,
reco pgvector, agent) : [`docs/`](docs/). Support de pitch : [`docs/prez/`](docs/prez/).
Problèmes rencontrés au test & correctifs (movie_age, juge, modèle 7B) :
[`docs/ajustements-agent.md`](docs/ajustements-agent.md).

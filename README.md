# HorRAGor2 — L'Agent de l'Horreur 👻

Agent conversationnel RAG (LangGraph, boucle ReAct + Juge déterministe) sur une base de
films d'horreur, exposé via une **API FastAPI** asynchrone et une **interface de chat Streamlit**.

Stack : LangGraph · Ollama (LLM + embeddings, local) · FAISS · Supabase (SQL + pgvector) · FastAPI · Streamlit · uv.

> **Prérequis IA (local, sans clé API)** : installer [Ollama](https://ollama.com), puis
> `ollama pull llama3.2:3b` et `ollama pull nomic-embed-text` (embeddings 768 dim).

## Démarrage rapide

```bash
# 1. Installer les dépendances (crée le venv)
uv sync --extra dev

# 2. Copier la config et la remplir
cp .env.example .env

# 3. Lancer l'API (terminal 1)
uv run horragor-api          # http://127.0.0.1:8000  (/health, /chat)

# 4. Lancer l'interface (terminal 2, DEPUIS LA RACINE du projet)
uv run streamlit run src/front/streamlit/app.py
```

> ⚠️ Lancer Streamlit **depuis la racine** du projet : c'est là que se trouve
> `.streamlit/config.toml` (thème sombre « Chat Horror ») que Streamlit applique au démarrage.

> Dès maintenant, l'API et l'UI fonctionnent grâce à un **faux moteur**
> (`backend/mocks/fake_engine.py`) qui renvoie une réponse de test — sans LLM ni base.
> Le vrai agent LangGraph arrivera au temps 2.

## Qualité

```bash
uv run ruff check .
uv run pytest -q
```

## Structure

Deux packages sous `src/` : **`front`** (interface) et **`backend`** (toute la logique métier).

```
src/
├── front/                 👤 A — Front-End (organisé par techno)
│   ├── common/            ·   client HTTP partagé (réutilisable par un futur Gradio)
│   └── streamlit/         ·   front Streamlit (app.py)
└── backend/
    ├── config.py          🤝 réglages centraux (.env)
    ├── contracts/         🤝 schémas Pydantic + interfaces (figé en premier)
    ├── mocks/             🤝 faux moteur + fixtures
    ├── api/               👤 B — FastAPI async (/health, /chat)
    ├── data/              👤 C — Supabase (SQL + pgvector) + index FAISS
    ├── tools/             🤝 temps 2 — les outils de l'agent
    └── agent/             🤝 temps 2 — boucle ReAct + Juge
```

Le **Front** ne contient aucune logique métier : il appelle l'API en HTTP et réutilise les
`contracts` du Back-End comme unique source de vérité sur la forme des données (PDF :
« découplage strict »). Toutes les clés / accès Supabase sont **confinés au Back-End**.

### Les outils de l'agent (temps 2, noms du PDF)

| Outil | Fichier | Rôle |
|---|---|---|
| Routeur FAISS | `tools/faiss_tool.py` | `validate_film` — valide l'existence (Nom → ID) |
| `query_movie_metadata` | `tools/sql_tool.py` | Métadonnées (réalisateur, année, genre, note, casting) |
| `find_similar_horror_movies` | `tools/pgvector_tool.py` | Reco sémantique (pgvector, cosinus) |
| `scrape_detailed_synopsis` | `tools/wikipedia_tool.py` | Scraping Wikipédia à la demande |
| `calculate_movie_age` | `tools/temporal_tool.py` | Âge du film (Python natif) — **déjà implémenté** |
| `horror_survival_simulator` | `tools/survival_tool.py` | Optionnel — simulateur ludique |

## Workflow Git

Publication initiale (superviseur, une seule fois — dépôt **public**, projet de cours) :

```bash
gh repo create horragor2 --public --source=. --push
```

Puis : branches `feat/<brique>-<sujet>` → Pull Request → review du superviseur → merge sur `main`.
On ne modifie pas `backend/contracts/` sans prévenir l'équipe.

> Dépôt public : aucun secret ne doit être commité. Les clés vivent dans `.env`
> (ignoré par git) ; seul `.env.example`, sans valeurs, est versionné.

Architecture détaillée et diagrammes : [`docs/`](docs/).

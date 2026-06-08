# Guide de démarrage — installer, lancer, contribuer

Pas à pas pour mettre en route le projet et travailler à plusieurs.
Dépôt : `https://github.com/os974/horragor2`. Vue d'ensemble : [`../README.md`](../README.md).

---

## 1. Installation (une fois par poste)

```bash
git clone https://github.com/os974/horragor2.git
cd horragor2
uv sync --extra dev

# IA locale (Ollama) : https://ollama.com
ollama pull qwen2.5:7b        # agent (ReAct) + juge (anti-hallucination)
ollama pull nomic-embed-text  # embeddings (768 dim)

cp .env.example .env          # le .env n'est JAMAIS commité
```

À renseigner dans `.env` :
- `DATABASE_URL` — connexion Supabase (`postgresql+psycopg://…`), **requise** ;
- `TMDB_TOKEN` — token v4 TMDB, **optionnel** (réalisateur + casting).

> Les autres réglages (port, modèles…) ont un défaut dans `src/backend/config.py` :
> n'ajouter une ligne dans `.env` QUE pour **surcharger** un défaut (ex. `API_PORT=8001`
> si le port 8000 est déjà pris).

Vérifier l'installation : `uv run pytest -q` (la suite doit être verte).

## 2. Préparation des données (une fois)

```bash
uv run horragor-faiss            # index FAISS des titres (routeur)
uv run horragor-pgvector-setup   # active pgvector + table movie_embeddings
uv run horragor-embeddings       # vectorise les synopsis (reco) — ~6 min
```

## 3. Lancer l'application

```bash
# Terminal 1 — API (agent)
uv run horragor-api
# Terminal 2 — interface (DEPUIS LA RACINE, pour le thème sombre)
uv run streamlit run src/front/streamlit/app.py   # -> http://localhost:8501
```

---

## 4. Travailler à plusieurs (workflow Git)

Le code est organisé par brique (`front`, `api`, `data`, `agent`) pour avancer en parallèle.

```bash
# Démarrer une tâche : partir d'un main à jour
git switch main && git pull
git switch -c feat/<brique>-<sujet>      # ex. feat/front-historique
```

**Boucle quotidienne :**
```bash
uv run ruff check . && uv run pytest -q  # 1. vérifier
git add -p                                # 2. choisir ses changements
git commit -m "feat(front): ..."          # 3. committer
git push -u origin feat/ma-branche        # 4. pousser
# 5. ouvrir une Pull Request → review → merge sur main
```

**Anti-conflits** (après chaque merge d'un collègue) :
```bash
git switch main && git pull
git switch -            # revenir sur sa branche
git merge main          # réintégrer tôt et souvent = peu de conflits
```

> Règle d'or : on ne modifie pas `src/backend/contracts/` sans prévenir l'équipe (tout en dépend).
> Dépôt public : aucun secret commité (clés dans `.env`, ignoré par git).

---

## Aide-mémoire des commandes

| Besoin | Commande |
|---|---|
| Lancer l'API | `uv run horragor-api` |
| Lancer l'interface | `uv run streamlit run src/front/streamlit/app.py` |
| Construire l'index FAISS | `uv run horragor-faiss` |
| Préparer / remplir pgvector | `uv run horragor-pgvector-setup` puis `uv run horragor-embeddings` |
| Tester la recherche FAISS | `uv run horragor-search "the thing"` |
| Exporter le schéma du graphe | `uv run horragor-graph` |
| Lire la trace du dernier run | `uv run horragor-trace` (`-n N` pour les N derniers) |
| Tests / style | `uv run pytest -q` · `uv run ruff check .` |
| Ajouter une dépendance | `uv add <paquet>` |

# Guide de démarrage — pas à pas (équipe de 3, débutants)

Ce guide donne l'ordre exact des étapes pour démarrer le projet et travailler à 3 sans se
bloquer. Dépôt : `https://github.com/os974/horragor2`.

> Convention de branches : `feat/<brique>-<sujet>` (ex. `feat/front-affichage`).
> Règle d'or : on ne modifie pas `src/backend/contracts/` sans prévenir l'équipe.

---

## 🟢 Phase commune — à faire UNE fois par chacun

```bash
# 1. Récupérer le projet
git clone https://github.com/os974/horragor2.git
cd horragor2

# 2. Installer l'environnement Python (crée le .venv)
uv sync --extra dev

# 3. Installer l'IA locale (Ollama) puis tirer les modèles
#    -> https://ollama.com
ollama pull llama3.2:3b
ollama pull nomic-embed-text

# 4. Préparer la config locale (le .env n'est jamais commité)
cp .env.example .env

# 5. Vérifier que tout marche
uv run pytest -q          # doit afficher "6 passed"
```

---

## 👤 A — Front / Streamlit

```bash
git switch main && git pull              # partir d'un main à jour
git switch -c feat/front-affichage       # SA branche
```

Première tâche : lancer l'app et enrichir l'affichage.

```bash
# Terminal 1 : l'API (mockée pour l'instant)
uv run horragor-api
# Terminal 2 : l'interface (depuis la racine, pour le thème .streamlit/)
uv run streamlit run src/front/streamlit/app.py
```

- Vérifier le **thème sombre** « Chat Horror ».
- Dans `src/front/streamlit/app.py` : afficher le `verdict` du Juge + un bouton
  « Nouvelle conversation » (reset de `session_state`).

## 👤 B — API / FastAPI

```bash
git switch main && git pull
git switch -c feat/api-erreurs
```

- Gestion d'erreurs dans `src/backend/api/routes.py` (moteur qui échoue → code HTTP propre).
- Garder `src/backend/api/deps.py` comme **seul** point de bascule mock → vrai agent.
- Ajouter 1-2 tests dans `tests/test_api.py` ; explorer `http://127.0.0.1:8000/docs`.

## 👤 C — Data / FAISS (prioritaire)

```bash
git switch main && git pull
git switch -c feat/data-supabase
uv add supabase                          # ajoute le client Supabase
```

- Côté Supabase : créer la table `films`, activer pgvector, colonne `embedding vector(768)`.
- Dans `src/backend/data/db.py` : initialiser le client depuis `settings` et implémenter
  `get_metadata` / `validate_film`.
- Vérif : `get_metadata(1)` renvoie un `FilmMetadata` depuis Supabase.

---

## 🔁 La boucle quotidienne (chacun, en répétition)

```bash
uv run ruff check . && uv run pytest -q       # 1. vérifier
git add -p                                     # 2. sélectionner ses changements
git commit -m "feat(front): affichage du verdict"   # 3. committer
git push -u origin feat/ma-branche             # 4. pousser
# 5. ouvrir une Pull Request sur GitHub → review → merge
```

## 🧭 Règle anti-conflits (cruciale à 3)

Après **chaque** merge d'un collègue :

```bash
git switch main && git pull
git switch feat/ma-branche
git merge main          # réintégrer tôt et souvent = peu de conflits
```

---

## Aide-mémoire des commandes utiles

| Besoin | Commande |
|---|---|
| Lancer l'API | `uv run horragor-api` |
| Lancer l'interface | `uv run streamlit run src/front/streamlit/app.py` |
| Lancer les tests | `uv run pytest -q` |
| Vérifier le style | `uv run ruff check .` |
| Ajouter une dépendance | `uv add <paquet>` |
| Mettre à jour sa branche | `git switch main && git pull && git switch - && git merge main` |

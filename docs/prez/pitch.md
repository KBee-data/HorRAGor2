---
marp: true
theme: default
paginate: true
backgroundColor: '#111111'
color: '#e2e8f0'
style: |
  section { font-size: 26px; }
  h1, h2 { color: #ff4d4d; }
  strong { color: #ff8080; }
  code { color: #e2e8f0; background: #1b1f24; }
  a { color: #ff8080; }
---

<!-- _paginate: false -->

# HorRAGor 👻
## L'Agent de l'Horreur

Agent conversationnel **RAG** spécialisé films d'horreur
— **0 % hallucination**, 100 % local.

<br>

*Équipe : … · … · …* · Soutenance Partie 2

---

# Le défi

Construire un **agent conversationnel autonome** sur une base de **33 961 films d'horreur**, capable de :

- répondre **factuellement** (réalisateur, année, genre, casting…)
- **recommander** des films proches sémantiquement
- chercher des détails **à la demande** (Wikipédia)
- **ne jamais inventer** : 0 % d'hallucination, ou dire « je ne sais pas »

> Le tout **en local** (aucune clé API, aucun coût) et **industrialisé**.

---

# Architecture — full-stack IA

```
Utilisateur
   │
[ Streamlit ]  ──HTTP──▶  [ FastAPI async ]  ──▶  [ Agent LangGraph ]
  front                      /chat                   ReAct + Juge
                                                       │   │
                                          ┌────────────┘   └───────────┐
                                       [ Tools ]                    [ Juge LLM ]
                              FAISS · SQL+TMDB · pgvector · Wiki
                                          │
                                  [ Supabase Postgres ]
```

**Découplage strict** : le front ne fait que du HTTP · les secrets restent au back-end.

---

# La donnée (brique C)

| Brique | Rôle |
|---|---|
| **FAISS** (RAM) | routeur : valide un titre → `id` (matching flou, 33 961 titres) |
| **SQL** (SQLAlchemy) | métadonnées brutes (année, genres, note, synopsis) |
| **TMDB** | réalisateur + casting (absents de la base → enrichis) |
| **pgvector** | reco sémantique : 31 284 vecteurs de synopsis, similarité cosinus |

Embeddings **locaux** (`nomic-embed-text`, 768 dim) · base **Supabase** héritée de la Partie 1.

---

# L'agent ReAct (LangGraph)

```
START → agent ⇄ tools → juge → réponse | correction | fallback
```

- **Cerveau** : `llama3.2:3b` (local, Ollama) — *Reason + Act*
- **4 outils par titre** : `lookup_movie`, `find_similar`, `movie_age`, `wikipedia_synopsis`
- 🔑 *Enseignement* : un petit modèle **chaîne mal les `id`** → on lui donne des outils
  **par titre** qui composent les fonctions data en interne → **bien plus fiable**

---

# Anti-hallucination : le Juge

Un **2ᵉ modèle distinct** (`qwen2.5:3b`) audite chaque réponse :

- est-elle **fidèle** aux données des outils ? **cohérente** avec la question ?
- sinon → l'agent **corrige** (boucle bornée) → puis **fallback** honnête

**Exemple réel** — requête « jason » :
- ❌ avant (juge déterministe) : *« Halloween a 48 ans »* validé à tort
- ✅ après (juge LLM) : **rejeté** → *« je ne peux pas garantir… »*

---

# Industrialisation

- **`uv`** : env reproductible, `pyproject.toml`, lockfile
- **Tests** (pytest) + **lint** (ruff) + **CI GitHub Actions**
- **API async** : l'agent tourne dans un thread → **aucun gel** d'écran
- **Robustesse** : l'API ne renvoie jamais de 500 (erreurs agent capturées)
- **100 % local & gratuit** (Ollama) · **secrets** confinés au `.env` (jamais commités)
- **Git propre** : branches + PR + un commit par étape, journaux de dev

---

# Démo 🎬

1. **Fait** : « Qui a réalisé Hereditary et en quelle année ? »
   → *Ari Aster, 2018* · `verdict: valid`
2. **Reco** : « Des films similaires à Alien ? »
   → voisins sémantiques (sci-fi / créature)
3. **Garde-fou** : film inexistant → *« je ne connais pas ce film »*
4. **Juge** : une requête piège → **fallback** (pas d'invention)

---

# Choix & enseignements

- **Outils par titre** > chaînage d'`id` pour un petit modèle
- **Juge ≠ agent** : un modèle ne doit pas juger ses propres réponses
- **SQLAlchemy + connection string** (continuité Partie 1) > SDK pour du relationnel
- **pgvector** : la reco vit dans la base, pas en Python (sous-requête `<=>`)
- **Mocks + contrats** : 3 personnes en parallèle sans se bloquer

---

# Perspectives & merci

**Pistes** : mémoire conversationnelle multi-tours · streaming des réponses ·
juge encore plus fin · déploiement (Docker).

<br>

# Questions ? 👻

*Démo live + code : dépôt Git*


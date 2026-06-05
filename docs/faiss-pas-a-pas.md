# FAISS — journal pas à pas

Construction du **routeur de validation de titres** : un index FAISS en RAM des couples
**[titre : id]** qui valide l'existence d'un film et renvoie son `id` (tool `validate_film`).
Ce document est complété **à chaque étape** (= chaque commit de la branche `feat/faiss-index`).

Contexte technique :
- Embeddings via **Ollama** `nomic-embed-text` (**768 dim**), choix d'équipe.
- Source des titres pour le dev : **SQLite de Part 1** (`HorRAGor1/data/horragor.db`, 33 961 films),
  en attendant la connexion Supabase. Source rendue configurable pour basculer plus tard.

---

## Étape 1 — Helper d'embedding Ollama

**But :** une fonction unique qui transforme du texte en vecteur, réutilisable pour les titres
(FAISS) et plus tard les synopsis (pgvector).

**Ce que je fais :**
- `src/backend/data/embed.py` :
  - `embed_texts(texts) -> list[list[float]]` : appelle Ollama `POST /api/embed` en **batch**
    (champ `input`), avec **repli** sur l'endpoint legacy `/api/embeddings` si l'instance est
    ancienne (404).
  - `embed_text(text)` : raccourci pour un seul texte.
  - **Garde-fou de dimension** : si Ollama renvoie une taille ≠ `settings.embedding_dim` (768),
    on lève une erreur explicite (évite une incohérence silencieuse avec l'index / pgvector).
- `tests/test_embed.py` : l'appel HTTP est **moqué** (la CI n'a pas Ollama). On vérifie la forme
  du résultat, le court-circuit sur liste vide, et l'erreur en cas de mauvaise dimension.

**Pourquoi ces choix :**
- *Batch* : embedder 33 961 titres un par un serait lent (overhead HTTP) ; le batch réduit ça.
- *Centralisation* : un seul point garantit que build et requête utilisent le même modèle.
- *Mock en test* : tests rapides, déterministes et exécutables sans GPU/modèle.

**Vérifier :** `uv run pytest -q tests/test_embed.py` et `uv run ruff check .`.

**Mesure réelle (RTX 5060, modèle sur GPU) :**
- 1 requête de 200 titres en série : ~7 titres/s (un seul `input` n'est pas parallélisé par Ollama).
- 10 requêtes parallèles (chunks de 20) : pic mesuré ~228 titres/s (à chaud).
- Conclusion : à l'étape 3, on embeddera en **requêtes concurrentes** (ThreadPool), pas en un seul gros batch.
- ⚠️ En build réel (étape 3), le débit soutenu est plus modéré (~35/s, cf. ci-dessous) → on garde la concurrence et c'est ajustable via le nombre de workers.

---

## Étape 2 — Chargeur de titres (source configurable)

**But :** fournir la liste des couples `(id, titre)` qui alimentera l'index, derrière une
interface stable, pour pouvoir changer de source (SQLite Part 1 → Supabase) sans rien casser.

**Ce que je fais :**
- `config.py` : 3 réglages — `titles_db_path` (défaut = SQLite de Part 1, résolu depuis la
  racine, surchargé via `.env`), `faiss_index_dir` (`faiss_index/`, déjà gitignoré),
  `faiss_score_threshold` (0.75).
- `src/backend/data/titles.py` : `load_titles(db_path=None) -> list[(id, title)]` lit
  `SELECT id, title FROM movies` en **SQLite read-only** (`mode=ro`), titres vides exclus.
- `tests/test_titles.py` : crée un mini SQLite temporaire et vérifie le chargement + l'erreur
  si le fichier est absent (aucune dépendance à la vraie base).

**Pourquoi ces choix :**
- *Interface stable* : le build et le tool ne connaissent que `load_titles()`, pas la source.
- *Read-only* : on ne risque jamais d'altérer la base de Part 1.
- *Chemin configurable* : chacun peut pointer son propre SQLite, et on basculera sur Supabase
  en ne modifiant que ce module.

**Vérifier :** `uv run pytest -q tests/test_titles.py`.


---

## Étape 3 — Build de l'index FAISS

**But :** transformer les titres en index vectoriel interrogeable, persisté sur disque.

**Ce que je fais :**
- `src/backend/data/faiss_index.py` — classe `TitleIndex` :
  - `build_from_pairs(pairs)` : normalise les titres, **embedde en concurrence** (ThreadPool),
    **L2-normalise** les vecteurs et construit `faiss.IndexFlatIP(768)` (= cosinus exact).
  - `search_vector(vec, k)` : recherche les k plus proches (prend un vecteur déjà calculé →
    module testable sans Ollama).
  - `save()/load()/exists()` : persistance dans `faiss_index/` (index `.index` + mapping JSON).
- `src/backend/data/build_faiss.py` : CLI `horragor-faiss [--limit N]` (load → build → save).
- `tests/test_faiss.py` : vecteurs déterministes (pas d'Ollama) — recherche du plus proche,
  distinction de vecteurs, aller-retour save/load.

**Pourquoi ces choix :**
- *IndexFlatIP + L2-normalisation* = cosinus exact, simple, parfait pour ~34k titres en RAM.
- *Embedding concurrent* : tient compte de la mesure de l'étape 1.
- *Persistance* : on construit une fois, on recharge instantanément (pas de ré-embedding au boot).

**Mesure réelle (sous-ensemble) :** 500 titres construits en **14 s** (~35/s) → build complet
des 33 961 ≈ **~16 min** (ajustable via `workers`). Index + mapping écrits dans `faiss_index/`
(gitignoré).

**Sanity end-to-end (index de 500) :**
```
'the mortuary assistant' -> score=1.000 id=2  ('The Mortuary Assistant')   # match exact
'scream 7'               -> score=1.000 id=8  ('Scream 7')                  # match exact
'film inexistant xyz'    -> score=0.603 id=108 ('Inexorable')              # < seuil 0.75 -> None
```
→ Le seuil **0.75** sépare bien un vrai film (~1.0) d'un titre absent (~0.60).

**Build complet :** `uv run horragor-faiss` (job ponctuel, ~16 min, GPU). Pour le dev des
étapes suivantes, l'index de 500 titres déjà présent suffit.

**Vérifier :** `uv run pytest -q tests/test_faiss.py`.

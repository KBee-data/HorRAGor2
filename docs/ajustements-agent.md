# Ajustements de l'agent — problèmes rencontrés & correctifs

Après l'implémentation de l'agent, les **tests réels** ont révélé des réponses incorrectes
(souvent un « je ne sais pas » à tort). Le diagnostic s'est fait via la **trace profonde**
(`logs/traces.jsonl`, `uv run horragor-trace`), qui montre chaque étape interne
(outil → FAISS → SQL → TMDB → pgvector → juge → verdict). Sans elle, on ne voyait qu'une
réponse opaque ; avec elle, chaque cause est visible noir sur blanc.

---

## 1. `movie_age` inventait l'année (piège)

- **Symptôme** : « Quel âge a Alien ? » → `fallback`.
- **Trace** : `movie_age(release_year='1979')` appelé **directement**, sans `lookup_movie` →
  année **devinée** par le modèle → réponse non ancrée → le juge rejette (rien ne prouve que
  1979 = Alien).
- **Cause** : `movie_age(année)` laissait le LLM passer une année hallucinée (le seul outil
  encore basé sur une valeur brute).
- **Correctif** : **`movie_age(titre)`** — va chercher l'année **en base** lui-même
  (auto-ancré, comme les autres outils).

## 2. Le juge LLM sur-rejetait (il recalculait)

- **Symptôme** : des réponses **correctes** finissaient en `fallback`.
- **Trace** : `calculate_movie_age 2026-1979 = 47` (correct), mais
  `judge → rejeté : « 47 est incorrect, devrait être 50 / en 2023 »`.
- **Cause** : le juge (`qwen2.5:3b`) **refaisait ses propres calculs** (faux) et contredisait
  la donnée pourtant ancrée.
- **Correctif** : **prompt du juge durci** — interdit de recalculer ou d'utiliser ses
  connaissances ; une valeur présente dans les DONNÉES est correcte par définition ; *dans le
  doute → valide*. (C'était probablement le plus gros pourvoyeur de faux « je ne sais pas ».)

## 3. `find_similar` : résultats non restitués

- **Symptôme** : « Films similaires à The Thing » → `fallback`.
- **Trace** : `find_similar → pgvector → 3 films` (l'outil marche !), mais l'agent répondait
  « je ne connais aucun film similaire » et le juge s'embrouillait sur la **liste de dicts**.
- **Correctif** : `find_similar` renvoie **`{film, similaires:[titres]}`** (lisible) + consigne
  prompt « restitue explicitement le contenu des outils ».

## 4. Le modèle 3B ne synthétisait pas

- **Symptôme** : « Intrigue de Nosferatu d'après Wikipédia » → réponse vide
  « Puis-je vous aider ? » ; recommandations **enjolivées** (année/réalisateur inventés).
- **Cause** : `llama3.2:3b` **appelle bien les outils**, mais **décroche sur la synthèse**
  (restituer une liste ou un texte long). Le prompt n'y change rien — c'est une limite du modèle.
- **Correctif (1ʳᵉ tentative)** : agent → `mistral:7b` → bonne synthèse… mais a révélé le
  problème 5.

## 5. `mistral:7b` : tool-calls émis en TEXTE (non parsés)

- **Symptôme** : « Quel âge a Hereditary ? » → **aucun outil appelé** (3/3), réponse du type
  « je vais utiliser l'outil `movie_age`… » sans le faire.
- **Trace / spike** : le modèle générait pourtant l'appel, mais dans le **contenu** sous forme
  de JSON brut (`[{"name":"movie_age","arguments":{...}}]`, parfois en bloc ```), **pas** dans
  le format structuré → `tool_calls` vide côté langchain-ollama.
- **Cause** : le template de tool-calling de `mistral:7b` sur Ollama est **incompatible** avec
  le parseur. (`tool_choice` forcé n'est pas honoré non plus.)
- **Correctif** : **agent → `qwen2.5:7b`** → tool-calls **structurés corrects** + bonne synthèse.

## 6. Le juge 3B rejetait encore les âges corrects

- **Symptôme** : avec qwen2.5:7b en agent, « Quel âge a Hereditary ? » calculait bien `8 ans`
  mais finissait en `fallback`.
- **Cause** : le juge `qwen2.5:3b` restait trop faible — il second-devinait l'âge malgré la
  consigne « ne recalcule pas ».
- **Correctif** : **juge → `qwen2.5:7b`** (même modèle que l'agent). Toutes les questions de
  test passent alors correctement (faits, âge, recos, question composée, film inconnu).

---

## Configuration finale

- **Agent + Juge** : `qwen2.5:7b` (un seul modèle chargé, ~5 Go avec les embeddings → tient sur
  8 Go, pas de swap). Embeddings : `nomic-embed-text`.
- Juge = même modèle que l'agent : compromis VRAM ; son **rôle/prompt strict** (vérifier la
  fidélité aux données, ne rien recalculer) le distingue de l'agent.

## Compromis assumés

- `qwen2.5:7b` : plus **lent** qu'un 3B (premier appel = chargement VRAM). Acceptable vu la
  fiabilité gagnée (tool-calling + synthèse + jugement).
- Juge plus **indulgent** (« dans le doute → valide ») : moins de faux rejets.

## Enseignement principal

La **trace / les logs** ont été l'outil de débug clé. Et le choix du **modèle local** est
déterminant pour un agent ReAct : il faut un modèle dont le **format de tool-calling** est
correctement parsé par Ollama **et** qui sait **synthétiser** — `qwen2.5:7b` coche les deux,
là où llama3.2:3b (synthèse) et mistral:7b (tool-calls) échouaient chacun sur un axe.

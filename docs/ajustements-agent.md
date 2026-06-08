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
- **Correctif** : **agent → `mistral:7b`** (7B) → restitue correctement listes et synopsis,
  sans invention.

---

## Compromis assumés

- `mistral:7b` : plus **lent** (premier appel = chargement ~5 Go en VRAM) et VRAM plus chargée
  (agent 7B + juge 3B ≈ 7 Go sur 8). Acceptable vu la fiabilité gagnée.
- Juge plus **indulgent** (« dans le doute → valide ») : moins de faux rejets, mais laisse
  passer de rares enjolivures — atténué par l'agent 7B qui n'enjolive plus.

## Enseignement principal

La **trace / les logs** ont été l'outil de débug clé : chaque cause (piège d'outil, juge qui
recalcule, modèle trop faible) était localisable précisément dans `logs/traces.jsonl`.

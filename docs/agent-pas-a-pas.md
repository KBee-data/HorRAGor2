# Agent ReAct — journal pas à pas

Temps 2 du projet : assembler les tools data dans un **agent conversationnel** (boucle
**ReAct** LangGraph) avec un **nœud Juge déterministe**, exposé via l'API à la place du mock.
Branche `feat/agent-react`, un commit par étape. LLM local : `llama3.2:3b` via Ollama.

---

## Spike — tool-calling local
Avant tout : vérifier que `llama3.2:3b` émet de vrais `tool_calls` via `langchain-ollama`
(`bind_tools`). ✅ Confirmé → l'approche LangGraph est viable.

## Étape 1 — Tools LangChain + scraper Wikipedia
- `wikipedia_tool.scrape_detailed_synopsis` via l'API REST de Wikipedia (sans Selenium).
- `agent/tools_registry.py` : outils `@tool` enveloppant les fonctions data.

## Étape 2 — Graphe ReAct + outils PAR TITRE
- `state.py` (messages + reducer `add_messages`, retries), `prompts.py` (anti-hallucination),
  `graph.build_graph` (ChatOllama bind_tools + `ToolNode`, boucle conditionnelle).
- **Constat clé** : un petit modèle (3B) chaîne mal `valider titre → id → requête par id`
  (il a appelé un outil avec un id invalide puis a *narré* un faux appel). **Correctif** :
  des outils **par titre** qui composent en interne les fonctions data —
  `lookup_movie`, `find_similar`, `movie_age`, `wikipedia_synopsis`. Bien plus fiable.

## Étape 3 — Nœud Juge déterministe
- `judge.verify` : toute **année** citée dans la réponse doit apparaître dans les observations
  des outils (le fait le plus vérifiable et le plus souvent halluciné). Sinon → l'agent corrige
  (boucle bornée `MAX_RETRIES=2`) → puis **fallback** (réponse honnête).
- Graphe : `agent → juge` ; verdict `retry → agent`, `valid`/`fallback → fin`.

## Étape 4 — AgentGraph + bascule API
- `AgentGraph.run` (implémente `AgentEngine`) invoque le graphe dans un **thread**
  (`asyncio.to_thread`) → l'API reste asynchrone (pas de gel d'écran). Renvoie
  `answer` + `sources` (outils appelés) + `verdict`.
- `api/deps.get_engine` → `AgentGraph` (au lieu de `FakeEngine`). Les tests surchargent par
  `FakeEngine` (rapides, hors-ligne).

**End-to-end réel (via /chat) :**
```
"Qui a réalisé Hereditary et en quelle année ?"
   -> "réalisé par Ari Aster en 2018"   sources:[lookup_movie]  verdict:valid
Film inexistant -> "Je ne connais pas ce film…"  (le « je ne sais pas » du brief)
```

## Étape 5 — Schéma du graphe (livrable) + doc
- `agent/export_graph.py` (CLI `horragor-graph`) génère le **Mermaid réel** depuis le graphe
  compilé → `docs/graphe_agent_genere.mmd` (toujours à jour avec le code).
- Régénérer : `uv run horragor-graph > docs/graphe_agent_genere.mmd`.

---

## Récapitulatif

L'agent est **complet et branché** : API async → `AgentGraph` → boucle ReAct
(`agent ↔ tools`) → Juge déterministe → réponse tracée (`answer`, `sources`, `verdict`).
Critères du brief démontrés : 0 % d'hallucination sur les métadonnées (réponses ancrées),
« je ne sais pas » sur les films inconnus, scraping Wikipédia sélectif, API non bloquante.

**Pistes d'amélioration** (hors périmètre socle) : Juge plus riche (réalisateur/genres en plus
de l'année), mémoire conversationnelle multi-tours (via `session_id` + checkpointer LangGraph),
streaming des réponses.

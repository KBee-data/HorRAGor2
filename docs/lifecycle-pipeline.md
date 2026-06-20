# Lifecycle des données — HorRAGor2

Deux flux cohabitent dans HorRAGor2 :
- **Préparation (offline)** : construire index FAISS + embeddings depuis Supabase
- **Requête (online)** : question → agent ReAct → outils → Supabase → réponse

---

## Lifecycle 1 — Préparation des données (commandes offline)

Exécutées une fois (ou après `horragor-reset-data`). Supabase est la source ET la destination
pour les embeddings.

### Fonctions

#### ① Index FAISS des titres (`uv run horragor-faiss`)

| Fonction | Fichier | Entrée | Sortie |
|---|---|---|---|
| `build(limit)` | `data/build_faiss.py` | `limit: int \| None` | — (effets disque) |
| `load_titles()` | `data/titles.py` | `DATABASE_URL` env | `list[tuple[int, str]]` (id, titre) |
| `TitleIndex.build_from_pairs(pairs, workers=10)` | `data/faiss_index.py` | `list[(int, str)]` | `TitleIndex` (IndexFlatIP L2-normalisé) |
| `normalize_title(title)` | `data/faiss_index.py` | `str` | `str` lowercase stripped |
| `embed_text(title)` | `data/embed.py` | `str` | `list[float]` 768 dims (nomic-embed-text) |
| `index.save()` | `data/faiss_index.py` | — | `faiss_index/titles.index` + `titles_map.json` |

#### ② Embeddings pgvector (`uv run horragor-embeddings`)

| Fonction | Fichier | Entrée | Sortie |
|---|---|---|---|
| `build(limit, batch=500)` | `data/build_embeddings.py` | `limit: int \| None`, `batch: int` | — (effets SQL) |
| `_load_overviews(limit)` | `data/build_embeddings.py` | `limit: int \| None` | `list[tuple[int, str]]` (id, overview) |
| `embed_texts_concurrent(texts, workers=10)` | `data/embed.py` | `list[str]` | `list[list[float]]` 768 dims |
| SQL UPSERT | `data/build_embeddings.py` | `(movie_id, vector)` | table `movie_embeddings` mise à jour |
| `CREATE INDEX movie_embeddings_hnsw` | `data/build_embeddings.py` | — | index HNSW cosinus sur `movie_embeddings` |

---

## Lifecycle 2 — Requête runtime (par question utilisateur)

### Fonctions

#### ① Streamlit UI → API

| Fonction | Fichier | Entrée | Sortie |
|---|---|---|---|
| `st.chat_input()` | `front/streamlit/app.py` | — | `prompt: str` |
| `send_message(message, session_id)` | `front/common/api_client.py` | `str`, `str` | `ChatResponse` |
| HTTP POST `/chat` | — | `ChatRequest` JSON | `ChatResponse` JSON |

#### ② FastAPI → Agent

| Fonction | Fichier | Entrée | Sortie |
|---|---|---|---|
| `chat(req, engine)` | `api/routes.py` | `ChatRequest`, `AgentEngine` | `ChatResponse` |
| `AgentGraph.run(req)` | `agent/graph.py` | `ChatRequest` | `ChatResponse` |
| `trace.begin()` | `backend/trace.py` | — | `list[TraceStep]` (collecteur ContextVar) |
| `asyncio.to_thread(graph.invoke, state)` | `agent/graph.py` | `AgentState` | `AgentState` final |

#### ③ Nœud Agent (LangGraph ReAct)

| Fonction | Fichier | Entrée | Sortie |
|---|---|---|---|
| `_agent_node(state)` | `agent/graph.py` | `AgentState` | `{"messages": [AIMessage]}` |
| `ChatOllama("qwen2.5:7b").bind_tools(TOOLS).invoke(messages)` | — | `list[Message]` | `AIMessage` (tool_calls ou texte final) |
| `_route_from_agent(state)` | `agent/graph.py` | `AgentState` | `"tools"` ou `"judge"` |

#### ④ Outils (ToolNode LangChain)

**Tool 1 : `lookup_movie(title: str) → dict`**

| Sous-fonction | Fichier | Entrée | Sortie |
|---|---|---|---|
| `faiss_tool.validate_film(title)` | `tools/faiss_tool.py` | `str` | `FilmRef \| None` |
| `embed_text(title)` | `data/embed.py` | `str` | `list[float]` 768d |
| `index.search_vector(vector, k=1)` | `data/faiss_index.py` | `list[float]` | `list[(score, id, title)]` |
| `sql_tool.query_movie_metadata(film_id)` | `tools/sql_tool.py` | `int` | `FilmMetadata \| None` |
| SQL JOIN movies+genres+ratings | Supabase | `film_id` | métadonnées complètes |
| `tmdb.get_credits(tmdb_id)` | `data/tmdb.py` | `int` | `{"director": str, "cast": list[str]}` |

**Tool 2 : `find_similar(title: str, k: int) → dict`**

| Sous-fonction | Fichier | Entrée | Sortie |
|---|---|---|---|
| `faiss_tool.validate_film(title)` | `tools/faiss_tool.py` | `str` | `FilmRef \| None` |
| `pgvector_tool.find_similar_horror_movies(film_id, k)` | `tools/pgvector_tool.py` | `int`, `int` | `list[FilmRef]` |
| SQL `ORDER BY embedding <=> (SELECT embedding … WHERE movie_id=:id)` | Supabase | `film_id`, `k` | k films les plus proches (cosinus) |

**Tool 3 : `movie_age(title: str) → dict`**

| Sous-fonction | Fichier | Entrée | Sortie |
|---|---|---|---|
| `faiss_tool.validate_film(title)` | `tools/faiss_tool.py` | `str` | `FilmRef \| None` |
| `sql_tool.query_movie_metadata(film_id)` | `tools/sql_tool.py` | `int` | `FilmMetadata \| None` |
| `temporal_tool.calculate_movie_age(release_year)` | `tools/temporal_tool.py` | `int` | `int` (âge en années) |

**Tool 4 : `wikipedia_synopsis(title: str) → str \| None`**

| Sous-fonction | Fichier | Entrée | Sortie |
|---|---|---|---|
| `wikipedia_tool.scrape_detailed_synopsis(title)` | `tools/wikipedia_tool.py` | `str` | `str \| None` |
| HTTP GET Wikipedia REST API summary | Wikipedia | slug titre | extract texte |

#### ⑤ Nœud Juge

| Fonction | Fichier | Entrée | Sortie |
|---|---|---|---|
| `_judge_node(state)` | `agent/graph.py` | `AgentState` | `{"verdict": str}` |
| `judge.evaluate(question, answer, tool_outputs)` | `agent/judge.py` | `str`, `str`, `list[str]` | `tuple[bool, str]` |
| `ChatOllama("qwen2.5:7b").with_structured_output(JudgeVerdict).invoke(…)` | — | messages | `JudgeVerdict(valid, reason)` |
| `_route_from_judge(state)` | `agent/graph.py` | `AgentState` | `"agent"` (retry) ou `END` |

#### ⑥ Réponse et persistance

| Fonction | Fichier | Entrée | Sortie |
|---|---|---|---|
| `trace.record(kind, name, detail)` | `backend/trace.py` | `str`, `str`, `str` | ajoute `TraceStep` au collecteur |
| `trace.log_trace(question, response)` | `backend/trace.py` | `str`, `ChatResponse` | ligne JSONL dans `logs/traces.jsonl` |
| `_render_trace(entry)` | `front/streamlit/app.py` | `dict` | expander Streamlit avec icônes |

---

## Diagramme Mermaid 1 — Préparation des données (offline)

```mermaid
flowchart TD
    subgraph DB_SRC["Supabase PostgreSQL (source)"]
        M1[("movies\nid · title · overview")]
    end

    subgraph FAISS["① horragor-faiss  build_faiss.build()"]
        F1["load_titles()\nSELECT id, title FROM movies\n→ list[(int, str)]"]
        F2["normalize_title(title)\n→ str lowercase stripped"]
        F3["embed_text(title)\nOllama nomic-embed-text\n→ list[float] 768d"]
        F4["TitleIndex.build_from_pairs(pairs)\nIndexFlatIP L2-normalisé\n→ TitleIndex objet"]
        F5["index.save()\n→ faiss_index/titles.index\n+ faiss_index/titles_map.json"]
        F1 --> F2 --> F3 --> F4 --> F5
    end

    subgraph EMBED["② horragor-embeddings  build_embeddings.build()"]
        E1["_load_overviews(limit)\nSELECT id, overview FROM movies\nWHERE overview IS NOT NULL\n→ list[(int, str)]"]
        E2["embed_texts_concurrent(texts, workers=10)\nThreadPoolExecutor → Ollama\n→ list[list[float]] 768d"]
        E3["SQL UPSERT movie_embeddings\nINSERT ... ON CONFLICT DO UPDATE\n→ N lignes insérées"]
        E4["CREATE INDEX movie_embeddings_hnsw\nUSING hnsw(embedding vector_cosine_ops)\n→ index ANN cosinus"]
        E1 --> E2 --> E3 --> E4
    end

    subgraph DB_DST["Supabase PostgreSQL (destination)"]
        M2[("faiss_index/\ntitles.index + titles_map.json\n(disque local)")]
        M3[("movie_embeddings\nmovie_id · embedding vector(768)\n+ index HNSW")]
    end

    M1 --> F1
    M1 --> E1
    F5 --> M2
    E4 --> M3
```

---

## Diagramme Mermaid 2 — Requête runtime (online)

```mermaid
flowchart TD
    USER(["Utilisateur\nquestion texte libre"])

    subgraph UI["Streamlit  front/streamlit/app.py"]
        U1["st.chat_input()\n→ prompt: str"]
        U2["send_message(message, session_id)\nHTTP POST /chat\n→ ChatResponse"]
    end

    subgraph API["FastAPI  api/routes.py"]
        A1["chat(req: ChatRequest, engine)\n→ await engine.run(req)"]
    end

    subgraph GRAPH["AgentGraph.run()  agent/graph.py"]
        G1["trace.begin()\n→ list[TraceStep] via ContextVar"]
        G2["asyncio.to_thread(graph.invoke, AgentState)\nrecursion_limit=25"]
    end

    subgraph REACT["LangGraph ReAct loop"]
        subgraph AGT["Nœud Agent"]
            AG1["_agent_node(state)\nChatOllama qwen2.5:7b.bind_tools(TOOLS)\n→ AIMessage\ntool_calls OU texte final"]
            AG2{"_route_from_agent\ntool_calls ?"}
        end

        subgraph TOOLS["ToolNode — 4 outils"]
            subgraph LM["lookup_movie(title)"]
                LM1["validate_film(title)\nembed_text → FAISS search\n→ FilmRef | None"]
                LM2["query_movie_metadata(film_id)\nSQL JOIN movies+genres+ratings\n→ FilmMetadata"]
                LM3["get_credits(tmdb_id)\nTMDB API HTTP GET\n→ {director, cast}"]
                LM1 --> LM2 --> LM3
            end
            subgraph FS["find_similar(title, k=5)"]
                FS1["validate_film(title)\n→ FilmRef | None"]
                FS2["find_similar_horror_movies(film_id, k)\nSELECT ... ORDER BY embedding\n→ list[FilmRef]"]
                FS1 --> FS2
            end
            subgraph MA["movie_age(title)"]
                MA1["validate_film(title)\n→ FilmRef | None"]
                MA2["query_movie_metadata(film_id)\n→ FilmMetadata.release_year"]
                MA3["calculate_movie_age(release_year)\ncurrent_year - release_year\n→ int"]
                MA1 --> MA2 --> MA3
            end
            subgraph WK["wikipedia_synopsis(title)"]
                WK1["scrape_detailed_synopsis(title)\nHTTP GET Wikipedia REST API\n→ str | None"]
            end
        end

        subgraph JDG["Nœud Juge"]
            J1["_judge_node(state)\njudge.evaluate(question, answer, tool_outputs)\nChatOllama qwen2.5:7b.with_structured_output\n→ JudgeVerdict(valid, reason)"]
            J2{"_route_from_judge\nretry < 2 ?"}
        end
    end

    subgraph SUPABASE["Supabase PostgreSQL"]
        DB1[("movies · genres · ratings\nmovie_genres · movie_keywords")]
        DB2[("movie_embeddings\nvector(768) + index HNSW")]
        FAISS_DISK[("faiss_index/\ntitles.index (disque local)")]
    end

    subgraph RESP["Réponse + persistance"]
        R1["ChatResponse\nanswer · sources · verdict · trace"]
        R2["trace.log_trace(question, response)\n→ logs/traces.jsonl JSONL"]
        R3["Streamlit render\n_render_trace : expander icônes\n_render_meta : badge verdict"]
    end

    USER --> U1 --> U2 --> A1 --> G1 --> G2
    G2 --> AG1
    AG1 --> AG2
    AG2 -->|"tool_calls"| TOOLS
    AG2 -->|"pas de tool_calls"| J1
    TOOLS -->|"ToolMessage ajouté"| AG1

    LM2 --> DB1
    FS2 --> DB2
    MA2 --> DB1
    LM1 --> FAISS_DISK
    FS1 --> FAISS_DISK
    MA1 --> FAISS_DISK

    J1 --> J2
    J2 -->|"invalid + retry"| AG1
    J2 -->|"valid ou fallback"| R1
    R1 --> R2
    R1 --> U2
    U2 --> R3
    R3 --> USER
```

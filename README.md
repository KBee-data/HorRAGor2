# HorRAGor 👻 — Multi-Agent Gothic Horror Assistant (Partie 3)

[![Python 3.12](https://img.shields.io/badge/python-3.12-blue.svg)](https://www.python.org/downloads/)
[![LangGraph](https://img.shields.io/badge/LangGraph-Multi--Agent-orange.svg)](https://github.com/langchain-ai/langgraph)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688.svg)](https://fastapi.tiangolo.com)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.40+-FF4B4B.svg)](https://streamlit.io)
[![Tests](https://img.shields.io/badge/pytest-6%2F6%20passed-brightgreen.svg)]()

**HorRAGor** is a distributed **Multi-Agent Conversational AI** specialized in horror cinema lore. Powered by **LangGraph**, it coordinates specialized local researcher agents, live web scrapers, and an atmospheric Gothic Storyteller persona.

100% Local LLM inference via **Ollama** (`qwen2.5:7b` & `nomic-embed-text`) — no paid API keys required.

---

## 🏛️ Multi-Agent Architecture (LangGraph)

HorRAGor Part 3 decomposes monolithic RAG into three specialized, cooperative agents operating over a shared state graph:

```mermaid
flowchart TD
    UserQuery(["User Query / Question"]) --> RAGNode["🔎 1. RAG Agent (Local FAISS & SQL)"]
    
    RAGNode --> ConditionalRoute{"Is Local DB Lore Sufficient?"}
    
    ConditionalRoute -- "Yes (Complete DB Lore)" --> ContextTrimming["🧹 Context Trimming & Token Isolation"]
    ConditionalRoute -- "No (Missing / Offline DB)" --> ScraperNode["🌐 2. Scraper Agent (Wikipedia REST API)"]
    
    ScraperNode --> ContextTrimming
    ContextTrimming --> NarrationNode["🖋️ 3. Gothic Storyteller Agent (Atmospheric Prose)"]
    
    NarrationNode --> ChatOutput(["Final Atmospheric Narrative Response"])
```

### The 3 Specialized Agents

1. **🔎 RAG Agent (`rag_node`)**:
   * Resolves fuzzy movie titles against a local **FAISS vector index** (`faiss_index/`).
   * Queries structured SQL metadata (director, cast, genres, vote average, release year, local synopsis).
   * Generates vector similarity recommendations via **pgvector**.
2. **🌐 Scraper Agent (`scraper_node`)**:
   * Dynamically activates whenever local database facts are missing or incomplete.
   * Scrapes live plot overviews, trivia, and summaries from the **Wikipedia REST API** with intelligent disambiguation and film slug prioritization.
3. **🖋️ Narration Agent (`narration_node`)**:
   * Transforms raw factual summaries into chilling, atmospheric horror prose (Edgar Allan Poe / H.P. Lovecraft style).
   * **Adaptive Bilingualism**: Replies seamlessly in Victorian English or Gothic French matching the user's query language.

---

## 🛡️ Key Architectural & Engineering Innovations

* **🧹 Context Trimming & Token Isolation**:
  The Narration Agent never receives raw database logs, JSON structures, or API payloads. Only a clean, bulleted synthesis is injected into its context window, preventing prompt pollution and hallucination.
* **⚡ Offline Database Resilience & Graceful Failover**:
  Database connections to Supabase PostgreSQL use a non-blocking `connect_timeout=2`. If the remote database is paused or unreachable, the system automatically and seamlessly delegates synopsis retrieval to the Scraper Agent without raising 500 errors.
* **🧠 Short-Term Multi-Turn Conversational Memory**:
  Anaphora and pronoun references (*"Who directed The Thing?"* $\rightarrow$ *"What year was **it** released?"*) are automatically bound to the active film in memory across conversation turns.
* **⚡ High-Performance FAISS Preloading**:
  The FAISS index is loaded into RAM once during the asynchronous FastAPI **Lifespan** startup phase, enabling sub-millisecond vector title resolution.

---

## 📁 Repository Structure (Partie 3)

```text
horragor2_K/
├── src/
│   ├── models/
│   │   └── state.py              # HorragorState TypedDict (LangGraph shared memory)
│   ├── tools/
│   │   ├── rag_tool.py           # FAISS title matching + SQL lore extraction
│   │   └── scraper_tool.py       # Wikipedia REST API scraper with disambiguation
│   ├── graph/
│   │   ├── nodes.py              # 3 specialized agent node definitions
│   │   ├── router.py             # Conditional edge routing logic
│   │   └── pipeline.py           # LangGraph StateGraph assembly & async executor
│   ├── config.py                 # Pydantic BaseSettings & model temperatures
│   └── main.py                   # FastAPI server with lifespan FAISS preloading
├── tests/
│   └── test_multi_agent_pipeline.py  # 6 unit/integration tests (100% pass)
├── app_frontend.py               # Streamlit gothic horror UI with source badges
├── faiss_index/                  # Local FAISS index and titles map
└── docs/
    └── partie3-multi-agent-guide.md  # Comprehensive step-by-step developer guide
```

---

## 🚀 Quickstart & Installation

### 1. Prerequisites

* Python 3.11+ or 3.12
* [uv](https://docs.astral.sh/uv/) package manager
* [Ollama](https://ollama.com/) running locally with the following models:
  ```powershell
  ollama pull qwen2.5:7b
  ollama pull nomic-embed-text
  ```

### 2. Environment Setup

```powershell
# 1. Install dependencies
uv sync --extra dev

# 2. Configure environment variables
copy .env.example .env
```

Ensure `.env` contains:
```ini
DATABASE_URL=postgresql+psycopg://postgres.xxx:password@aws-1-eu-west-3.pooler.supabase.com:5432/postgres
OLLAMA_BASE_URL=http://localhost:11434
```

---

## 🖥️ Running the Application

Open two separate terminal windows:

### Terminal 1: FastAPI Backend Server

```powershell
.venv\Scripts\python.exe -m uvicorn src.main:app --reload --port 8000
```
* Interactive API Documentation: [http://localhost:8000/docs](http://localhost:8000/docs)
* Healthcheck: [http://localhost:8000/health](http://localhost:8000/health)

### Terminal 2: Streamlit Gothic Frontend

```powershell
.venv\Scripts\python.exe -m streamlit run app_frontend.py
```
* Opens the UI at [http://localhost:8501](http://localhost:8501)

---

## 🧪 Running the Test Suite

Execute the comprehensive test suite verifying conditional routing, context trimming, StateGraph compilation, anaphoric memory, and API endpoints:

```powershell
.venv\Scripts\python.exe -m pytest tests/test_multi_agent_pipeline.py -v
```

**Expected Output:**
```text
tests/test_multi_agent_pipeline.py::test_router_conditional_branching PASSED [ 16%]
tests/test_multi_agent_pipeline.py::test_context_summary_building PASSED     [ 33%]
tests/test_multi_agent_pipeline.py::test_pipeline_graph_structure PASSED     [ 50%]
tests/test_multi_agent_pipeline.py::test_fastapi_health_endpoint PASSED      [ 66%]
tests/test_multi_agent_pipeline.py::test_anaphoric_title_resolution PASSED   [ 83%]
tests/test_multi_agent_pipeline.py::test_fastapi_chat_endpoint_mocked PASSED [100%]

======================== 6 passed, 1 warning in 1.24s =========================
```

---

## 💡 Example Conversational Queries

* **English**:
  * *"Who directed the film The Thing?"*
  * *(Follow-up)* *"What year was it released?"*
  * *"Tell me about the 1979 horror film Alien."*
* **Français**:
  * *"Qui a réalisé Hereditary et que raconte ce film ?"*
  * *"Quels sont les films d'horreur similaires à The Shining ?"*

---

## 📜 Authors & Acknowledgments

* **Project**: HorRAGor Part 3 Multi-Agent Architecture
* **Stack**: LangGraph · FastAPI · Streamlit · Ollama · FAISS · Supabase · Wikipedia REST API

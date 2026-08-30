"""Configuration module for HorRAGor Part 3.

Loads environment variables and configuration settings for Ollama LLM,
FAISS vector index paths, database connections, and API server settings.
"""

from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

_PROJECT_ROOT = Path(__file__).resolve().parents[1]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=_PROJECT_ROOT / ".env",
        extra="ignore",
    )

    # --- API Server ---
    api_host: str = "127.0.0.1"
    api_port: int = 8000
    api_base_url: str = "http://127.0.0.1:8000"

    # --- Ollama Local LLMs ---
    ollama_base_url: str = "http://localhost:11434"
    llm_model: str = "qwen2.5:7b"
    # Specific temperature settings per agent role:
    rag_temperature: float = 0.0        # Deterministic factual extraction
    narration_temperature: float = 0.7  # Creative, immersive gothic storytelling

    # --- Embeddings & FAISS Index ---
    embedding_model: str = "nomic-embed-text"
    embedding_dim: int = 768
    faiss_index_dir: str = "data/faiss_index"
    faiss_score_threshold: float = 0.75

    # --- Database / Supabase (optional / inherited from Part 1 & 2) ---
    database_url: str = ""
    supabase_url: str = ""
    supabase_key: str = ""
    tmdb_token: str = ""
    tmdb_base_url: str = "https://api.themoviedb.org/3"

    @property
    def resolved_faiss_dir(self) -> Path:
        """Resolve FAISS index directory, supporting both data/faiss_index and faiss_index."""
        p = _PROJECT_ROOT / self.faiss_index_dir
        if p.exists():
            return p
        fallback = _PROJECT_ROOT / "faiss_index"
        if fallback.exists():
            return fallback
        return p


settings = Settings()

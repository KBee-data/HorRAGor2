"""Configuration centrale du Back-End.

POURQUOI pydantic-settings (et pas os.getenv partout) :
- typage + validation automatique des reglages (un port reste un int, etc.) ;
- chargement depuis .env, donc AUCUN secret ecrit en dur dans le code ;
- un seul objet `settings` importable partout = une seule source de verite.

Exigence du PDF (Encapsulation des acces Supabase) : les cles et l'init du client
Supabase sont CONFINEES au Back-End. C'est ici qu'elles vivent, jamais cote Front.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # extra="ignore" : on tolere des variables .env non listees ici sans planter.
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # --- Supabase (confine au Back-End) ---
    supabase_url: str = ""
    supabase_key: str = ""

    # --- API ---
    api_host: str = "127.0.0.1"
    api_port: int = 8000
    # URL de l'API telle que vue par le Front (sert au client HTTP Streamlit).
    api_base_url: str = "http://127.0.0.1:8000"

    # --- Modeles (choix d'equipe, encore a definir) ---
    llm_model: str = "a-definir"
    embedding_model: str = "a-definir"


# Instancie une fois au chargement du module : importer `settings` suffit partout.
settings = Settings()

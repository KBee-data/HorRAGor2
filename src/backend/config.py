"""Configuration centrale du Back-End.

POURQUOI pydantic-settings (et pas os.getenv partout) :
- typage + validation automatique des reglages (un port reste un int, etc.) ;
- chargement depuis .env, donc AUCUN secret ecrit en dur dans le code ;
- un seul objet `settings` importable partout = une seule source de verite.

STRATEGIE secrets vs reglages :
- SECRETS (cles, URLs privees) -> valeur UNIQUEMENT dans .env. Ici, defaut vide.
- REGLAGES non sensibles (port, modeles, host...) -> leur valeur par defaut vit
  ICI (source unique). Le .env ne sert qu'a SURCHARGER un defaut au besoin ;
  inutile donc de tous les redeclarer dans .env (sinon duplication).

Exigence du PDF (Encapsulation des acces Supabase) : les cles et l'init du client
Supabase sont CONFINEES au Back-End. C'est ici qu'elles vivent, jamais cote Front.
"""

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# Racine du projet : src/backend/config.py -> parents[2] = racine du depot.
# POURQUOI : ancrer .env a la racine le rend lisible quel que soit le dossier
# depuis lequel on lance la commande (sinon .env n'est cherche que dans le CWD).
_PROJECT_ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    # extra="ignore" : on tolere des variables .env non listees ici sans planter.
    model_config = SettingsConfigDict(env_file=_PROJECT_ROOT / ".env", extra="ignore")

    # --- Supabase : SECRETS (confines au Back-End) ---
    # Defaut vide : la vraie valeur DOIT etre fournie via .env (jamais commitee).
    #
    # ACCES PRINCIPAL a la base = connection string PostgreSQL (psycopg), via SQLAlchemy.
    # Choix impose par le brief Partie 1 ("Vous utiliserez SQLAlchemy ORM") et adapte au
    # schema relationnel (jointures genres/ratings, operateur pgvector). Voir
    # docs/connexion-supabase.md.
    # Ex : postgresql+psycopg://user:mdp@host:5432/postgres
    database_url: str = ""
    # SUPABASE_URL / SUPABASE_KEY : optionnels (API REST/Storage/Auth), PAS l'acces
    # principal a la base relationnelle.
    supabase_url: str = ""
    supabase_key: str = ""

    # --- TMDB : enrichissement realisateur/casting (absents de la base) ---
    # Token v4 (Bearer), confine au Back-End. Si vide, l'enrichissement est ignore
    # (director/cast restent vides) sans casser query_movie_metadata.
    tmdb_token: str = ""
    tmdb_base_url: str = "https://api.themoviedb.org/3"

    # --- API ---
    api_host: str = "127.0.0.1"
    api_port: int = 8000
    # URL de l'API telle que vue par le Front (sert au client HTTP Streamlit).
    api_base_url: str = "http://127.0.0.1:8000"

    # --- Modeles : stack 100% locale via Ollama (aucune cle API) ---
    # Ollama expose LLM et embeddings sur la meme instance locale.
    ollama_base_url: str = "http://localhost:11434"
    # LLM de l'agent (ReAct + tool-calling). qwen2.5:7b : tool_calls STRUCTURES corrects sur
    # Ollama (mistral les emettait en texte -> non parses) ET bonne synthese (≠ llama3.2:3b).
    llm_model: str = "qwen2.5:7b"
    # Modele du Juge (LLM-as-judge). qwen2.5:7b (meme que l'agent) : un 3B suivait mal la
    # consigne "ne recalcule pas" et rejetait des reponses correctes. Meme modele = un seul
    # chargement VRAM ; le prompt strict du juge suffit a distinguer son role de celui de l'agent.
    judge_model: str = "qwen2.5:7b"
    # Embeddings Ollama. nomic-embed-text -> 768 dimensions.
    embedding_model: str = "nomic-embed-text"
    # Dimension du vecteur : DOIT correspondre a la colonne pgvector vector(768)
    # ET a l'index FAISS. La changer impose de re-embedder toutes les donnees.
    embedding_dim: int = 768

    # --- FAISS (routeur de validation de titres) ---
    # Source des titres pour le DEV : SQLite de Part 1 (en attendant Supabase).
    # Chemin relatif resolu depuis la racine du projet ; surchargeable via .env.
    titles_db_path: str = "../HorRAGor1/data/horragor.db"
    # Dossier de persistance de l'index (gitignore : voir faiss_index/ dans .gitignore).
    faiss_index_dir: str = "faiss_index"
    # Seuil de similarite cosinus pour decider "ce film existe" (a calibrer).
    faiss_score_threshold: float = 0.75


# Instancie une fois au chargement du module : importer `settings` suffit partout.
settings = Settings()

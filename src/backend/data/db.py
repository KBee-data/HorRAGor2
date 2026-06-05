"""Engine SQLAlchemy partage vers la base (Supabase PostgreSQL via DATABASE_URL).

POURQUOI un engine unique mis en cache : SQLAlchemy gere un pool de connexions ;
on ne recree pas l'engine a chaque requete. `pool_pre_ping` revalide la connexion
avant usage (le pooler Supabase ferme les connexions inactives) — comme en Partie 1.

Choix de connexion : SQLAlchemy + connection string PostgreSQL (psycopg), conformement
au brief Partie 1. Voir docs/connexion-supabase.md.
"""

from functools import lru_cache

from sqlalchemy import Engine, create_engine

from backend.config import settings


@lru_cache(maxsize=1)
def get_engine() -> Engine:
    if not settings.database_url:
        raise RuntimeError(
            "DATABASE_URL non defini : renseignez-le dans .env "
            "(connection string Supabase, schema postgresql+psycopg://...)."
        )
    return create_engine(settings.database_url, pool_pre_ping=True, future=True)

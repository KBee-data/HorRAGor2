"""Chargement des couples (id, titre) — source des donnees du routeur FAISS.

COHERENCE DES IDS (critique) : l'index FAISS renvoie un `id` qui sert ensuite a
interroger les metadonnees. Cet `id` DOIT donc provenir de la MEME base que le
connecteur SQL. Les `id` du SQLite local de Part 1 ne correspondent PAS a ceux de
Supabase -> en presence d'une DATABASE_URL, on lit Supabase (source de verite).

Ordre de selection de la source :
1. `db_path` explicite  -> SQLite (override pour tests / dev hors-ligne) ;
2. `settings.database_url` defini -> Supabase (source de verite des ids) ;
3. sinon -> SQLite local par defaut (repli hors-ligne).
"""

import sqlite3
from pathlib import Path

from sqlalchemy import text

from backend.config import _PROJECT_ROOT, settings


def load_titles(db_path: str | None = None) -> list[tuple[int, str]]:
    """Renvoie la liste des (id, title) des films, titres non vides uniquement."""
    if db_path is not None:
        return _load_from_sqlite(db_path)
    if settings.database_url:
        return _load_from_database()
    return _load_from_sqlite(settings.titles_db_path)


def _load_from_database() -> list[tuple[int, str]]:
    """Lit (id, title) depuis la base relationnelle (Supabase) via SQLAlchemy."""
    from backend.data.db import get_engine

    with get_engine().connect() as conn:
        rows = conn.execute(
            text("select id, title from movies where title is not null and title <> ''")
        ).all()
    return [(int(i), str(t)) for i, t in rows]


def _resolve_db_path(db_path: str) -> Path:
    p = Path(db_path)
    # Chemin relatif -> ancre a la racine du projet (cf. config._PROJECT_ROOT).
    return p if p.is_absolute() else (_PROJECT_ROOT / p).resolve()


def _load_from_sqlite(db_path: str) -> list[tuple[int, str]]:
    path = _resolve_db_path(db_path)
    if not path.exists():
        raise FileNotFoundError(
            f"Base des titres introuvable : {path}. "
            "Renseignez TITLES_DB_PATH dans .env ou pointez vers le SQLite de Part 1."
        )
    # uri=True + mode=ro : ouverture en lecture seule, sans creer de fichier.
    con = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
    try:
        rows = con.execute(
            "SELECT id, title FROM movies WHERE title IS NOT NULL AND title <> ''"
        ).fetchall()
    finally:
        con.close()
    return [(int(i), str(t)) for i, t in rows]

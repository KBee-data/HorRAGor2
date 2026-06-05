"""Chargement des couples (id, titre) — source des donnees du routeur FAISS.

POURQUOI un module dedie derriere une fonction stable `load_titles()` :
aujourd'hui la source est le SQLite local de Part 1 (la connexion Supabase reelle
est encore a trancher). En isolant la lecture ici, on basculera plus tard sur
Supabase sans toucher au build de l'index ni au tool.

Lecture en SQLite READ-ONLY (mode=ro) : on ne modifie jamais la base de Part 1.
"""

import sqlite3
from pathlib import Path

from backend.config import _PROJECT_ROOT, settings


def _resolve_db_path(db_path: str | None) -> Path:
    raw = db_path or settings.titles_db_path
    p = Path(raw)
    # Chemin relatif -> ancre a la racine du projet (cf. config._PROJECT_ROOT).
    return p if p.is_absolute() else (_PROJECT_ROOT / p).resolve()


def load_titles(db_path: str | None = None) -> list[tuple[int, str]]:
    """Renvoie la liste des (id, title) des films, titres non vides uniquement."""
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

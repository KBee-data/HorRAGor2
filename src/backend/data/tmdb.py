"""Enrichissement via l'API TMDB : realisateur + casting (absents de la base).

POURQUOI : le brief demande realisateur/casting dans les metadonnees, mais la base
ne les contient pas. Chaque film a en revanche son `tmdb_id` -> on interroge TMDB.
Authentification par token v4 (Bearer), confine au Back-End (cf. config.settings).
"""

import httpx

from backend.config import settings


def get_credits(tmdb_id: int, top_cast: int = 5) -> dict:
    """Renvoie {'director': str|None, 'cast': list[str]} pour un film TMDB.

    Donnee faisant autorite (respecte le "0% hallucination"). En cas de probleme
    reseau, l'appelant decide quoi faire (ici : enrichissement best-effort).
    """
    resp = httpx.get(
        f"{settings.tmdb_base_url}/movie/{tmdb_id}/credits",
        headers={"Authorization": f"Bearer {settings.tmdb_token}"},
        timeout=15,
    )
    resp.raise_for_status()
    data = resp.json()

    director = next(
        (c.get("name") for c in data.get("crew", []) if c.get("job") == "Director"),
        None,
    )
    cast = [c.get("name") for c in data.get("cast", [])[:top_cast] if c.get("name")]
    return {"director": director, "cast": cast}

"""Tool 3 — scrape_detailed_synopsis : enrichissement a la demande (Wikipedia).

POURQUOI un declenchement STRICTEMENT selectif : le scraping est lent et gourmand en
contexte. On ne l'active que si l'utilisateur demande des details/anecdotes absents de
la base SQL, afin d'economiser la fenetre de contexte.

Implementation via l'API REST de Wikipedia (summary) plutot que Selenium : c'est plus
rapide, sans navigateur, et renvoie directement l'extrait de l'article.
"""

import httpx

from backend import trace

_WIKI_SUMMARY = "https://en.wikipedia.org/api/rest_v1/page/summary/"
# Wikipedia exige un User-Agent identifiant l'application.
_HEADERS = {"User-Agent": "HorRAGor2/0.1 (projet pedagogique)"}


def scrape_detailed_synopsis(title: str) -> str | None:
    """Renvoie l'extrait Wikipedia du film, ou None si introuvable / ambigu."""
    try:
        resp = httpx.get(
            _WIKI_SUMMARY + title.replace(" ", "_"),
            headers=_HEADERS,
            timeout=15,
            follow_redirects=True,
        )
    except httpx.HTTPError:
        trace.record("wikipedia", "scrape", f"{title!r} → erreur reseau")
        return None
    if resp.status_code != 200:
        trace.record("wikipedia", "scrape", f"{title!r} → introuvable (HTTP {resp.status_code})")
        return None
    data = resp.json()
    # Page d'homonymie -> pas un synopsis exploitable.
    if data.get("type") == "disambiguation":
        trace.record("wikipedia", "scrape", f"{title!r} → page d'homonymie")
        return None
    extract = data.get("extract") or None
    summary = f"extrait {len(extract)} car." if extract else "rien"
    trace.record("wikipedia", "scrape", f"{title!r} → {summary}")
    return extract

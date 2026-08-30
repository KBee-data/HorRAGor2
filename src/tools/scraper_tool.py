"""Native web scraper tool for online horror synopsis and trivia retrieval.

Uses the Wikipedia REST summary API to fetch detailed plot overviews
and production trivia when local database facts are missing or incomplete.
"""

from typing import Any
import httpx

_WIKI_SUMMARY = "https://en.wikipedia.org/api/rest_v1/page/summary/"
_HEADERS = {"User-Agent": "HorRAGor3/0.1 (multi-agent educational project)"}


def scrape_web_synopsis(title: str) -> dict[str, Any]:
    """Scrapes detailed movie synopsis and trivia from the Wikipedia REST API.

    Args:
        title: The movie title to look up on Wikipedia.

    Returns:
        A dictionary with keys `found` (bool), `title`, `content`, and optional `error`.
    """
    clean_title = title.strip().replace(" ", "_")
    url = f"{_WIKI_SUMMARY}{clean_title}"

    try:
        resp = httpx.get(url, headers=_HEADERS, timeout=12, follow_redirects=True)
    except httpx.HTTPError:
        return {
            "found": False,
            "title": title,
            "error": f"Network error when connecting to Wikipedia for '{title}'.",
            "content": "",
        }

    if resp.status_code != 200:
        return {
            "found": False,
            "title": title,
            "error": f"No Wikipedia article found for '{title}' (HTTP {resp.status_code}).",
            "content": "",
        }

    data = resp.json()
    if data.get("type") == "disambiguation":
        return {
            "found": False,
            "title": title,
            "error": f"Wikipedia page for '{title}' is a disambiguation page.",
            "content": "",
        }

    extract = data.get("extract", "").strip()
    if not extract:
        return {
            "found": False,
            "title": title,
            "error": f"No readable synopsis on Wikipedia for '{title}'.",
            "content": "",
        }

    return {
        "found": True,
        "title": data.get("title", title),
        "content": extract,
        "source": "Wikipedia",
    }

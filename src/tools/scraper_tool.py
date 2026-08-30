"""Native web scraper tool for online horror synopsis and trivia retrieval.

Uses the Wikipedia REST summary API to fetch detailed plot overviews
and production trivia when local database facts are missing or incomplete.
"""

from typing import Any
import httpx

_WIKI_SUMMARY = "https://en.wikipedia.org/api/rest_v1/page/summary/"
_HEADERS = {"User-Agent": "HorRAGor3/0.1 (multi-agent educational project)"}


def scrape_web_synopsis(title: str) -> dict[str, Any]:
    """Scrapes detailed movie synopsis and trivia from Wikipedia with disambiguation handling.

    Args:
        title: The movie title to look up on Wikipedia.

    Returns:
        A dictionary with keys `found` (bool), `title`, `content`, and optional `error`.
    """
    clean_base = title.strip().replace(" ", "_")

    # Prioritize film-specific slugs first to avoid dictionary redirects (e.g. Hereditary -> Heredity)
    candidate_slugs = [
        f"{clean_base}_(film)",
        f"{clean_base}_(1982_film)",
        f"{clean_base}_(movie)",
        f"{clean_base}_(horror_film)",
        clean_base,
    ]

    with httpx.Client(headers=_HEADERS, timeout=4.0, follow_redirects=True) as client:
        for slug in candidate_slugs:
            url = f"{_WIKI_SUMMARY}{slug}"
            try:
                resp = client.get(url)
                if resp.status_code == 200:
                    data = resp.json()
                    # Skip disambiguation pages and empty extracts
                    if data.get("type") == "disambiguation":
                        continue
                    extract = data.get("extract", "").strip()
                    if extract:
                        return {
                            "found": True,
                            "title": data.get("title", title),
                            "content": extract,
                            "source": "Wikipedia",
                        }
            except httpx.HTTPError:
                continue

        # Fallback: Wikipedia OpenSearch API to find the exact article title
        try:
            search_url = f"https://en.wikipedia.org/w/api.php?action=opensearch&search={clean_base}+film&limit=3&namespace=0&format=json"
            s_resp = client.get(search_url)
            if s_resp.status_code == 200:
                results = s_resp.json()
                if len(results) > 1 and results[1]:
                    matched_title = results[1][0].replace(" ", "_")
                    summary_resp = client.get(f"{_WIKI_SUMMARY}{matched_title}")
                    if summary_resp.status_code == 200:
                        data = summary_resp.json()
                        extract = data.get("extract", "").strip()
                        if extract and data.get("type") != "disambiguation":
                            return {
                                "found": True,
                                "title": data.get("title", title),
                                "content": extract,
                                "source": "Wikipedia",
                            }
        except Exception:
            pass

    return {
        "found": False,
        "title": title,
        "error": f"No Wikipedia article found for '{title}'.",
        "content": "",
    }

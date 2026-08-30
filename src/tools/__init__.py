"""Tools package for HorRAGor Part 3.

Exposes native tools for:
- search_local_rag: Local FAISS title resolution and database fact retrieval.
- scrape_web_synopsis: Live web scraping via Wikipedia API for missing or deep synopsis lore.
"""

from src.tools.rag_tool import search_local_rag
from src.tools.scraper_tool import scrape_web_synopsis

__all__ = ["search_local_rag", "scrape_web_synopsis"]

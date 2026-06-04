"""Tool 3 — scrape_detailed_synopsis : enrichissement a la demande (Wikipedia).

POURQUOI un declenchement STRICTEMENT selectif : le scraping (Selenium/Requests)
est lent et gourmand en contexte. On ne l'active que si l'utilisateur demande des
details/anecdotes absents de la base SQL, afin d'economiser la fenetre de contexte.
"""


def scrape_detailed_synopsis(title: str) -> str | None:
    """Renvoie un synopsis detaille depuis Wikipedia, ou None si introuvable."""
    # TODO (temps 2) : scraping cible de la page Wikipedia du film
    raise NotImplementedError

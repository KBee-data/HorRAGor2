"""Tool 4 — calculate_movie_age : calcul de l'age d'un film (Python natif).

POURQUOI une fonction Python deterministe (et pas une "estimation" du LLM) :
un calcul d'age doit etre exact et reproductible. On NE laisse jamais le LLM
faire l'arithmetique (risque d'erreur/hallucination) : le code la fait, l'agent
ne fait qu'appeler l'outil. C'est implementable des maintenant, sans dependance.
"""

from datetime import date

from backend import trace


def calculate_movie_age(release_year: int, current_year: int | None = None) -> int:
    """Renvoie l'age du film en annees (annee courante - annee de sortie).

    `current_year` est injectable pour rendre la fonction testable de maniere
    deterministe ; par defaut on prend l'annee reelle du jour.
    """
    if current_year is None:
        current_year = date.today().year
    age = current_year - release_year
    if age < 0:
        raise ValueError("L'annee de sortie est dans le futur.")
    trace.record("python", "calculate_movie_age", f"{current_year} - {release_year} = {age} ans")
    return age

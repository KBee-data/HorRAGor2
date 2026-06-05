"""Nœud Juge DETERMINISTE.

POURQUOI deterministe (du code, pas un 2e LLM) : on vise 0% d'hallucination sur les
metadonnees de base. Un second LLM pourrait lui-meme se tromper ; une verification
litterale est fiable, gratuite et reproductible.

Strategie concrete : l'ANNEE est le fait le plus verifiable et le plus souvent halluciné.
Le Juge verifie que toute annee (19xx/20xx) citee dans la reponse apparait bien dans les
observations des outils. Sinon -> rejet (l'agent corrige, boucle bornee ; puis fallback).
"""

import re

# Annee plausible de film : 19xx ou 20xx (groupe non capturant -> findall renvoie l'annee).
_YEAR_RE = re.compile(r"\b(?:19|20)\d{2}\b")

FALLBACK_ANSWER = "Desole, je ne peux pas garantir cette information de maniere fiable."


def verify(answer: str, tool_outputs: list[str]) -> bool:
    """True si la reponse est fidele : chaque annee citee est presente dans les outils."""
    answer_years = set(_YEAR_RE.findall(answer or ""))
    if not answer_years:
        return True  # aucune annee a verifier
    observed_years = set(_YEAR_RE.findall(" ".join(tool_outputs)))
    return answer_years.issubset(observed_years)

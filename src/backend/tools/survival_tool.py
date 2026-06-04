"""Tool 5 (OPTIONNEL) — horror_survival_simulator : outil ludique.

POURQUOI optionnel et isole : c'est un "bonus" de gameplay (le LLM estime les
chances de survie de l'utilisateur a partir du synopsis detaille du film). Il ne
participe pas au cœur factuel : on le garde a part pour ne pas alourdir l'agent.
"""


def horror_survival_simulator(synopsis: str) -> str:
    """Renvoie un scenario de survie ludique base sur le synopsis du film."""
    # TODO (temps 2, si retenu) : prompt dedie au LLM a partir du synopsis
    raise NotImplementedError

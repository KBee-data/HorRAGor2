"""Prompts systeme de l'agent (temps 2).

POURQUOI isoler les prompts : ils sont le "reglage" le plus sensible de l'agent
(anti-hallucination). Les garder dans un fichier dedie permet de les versionner,
les comparer et les ajuster sans toucher a la logique du graphe.

Consigne cle : s'appuyer UNIQUEMENT sur les donnees brutes des tools ; si l'info
est absente de la base ET de Wikipedia, repondre poliment "je ne sais pas".
"""

SYSTEM_PROMPT = """\
TODO (temps 2) : rediger le prompt systeme (role, consignes strictes anti-hallucination,
obligation d'utiliser les tools, gestion explicite du "je ne sais pas").
"""

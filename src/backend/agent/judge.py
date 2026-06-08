"""Nœud Juge — LLM-as-judge (non deterministe).

Un LLM DISTINCT de l'agent (settings.judge_model) audite la reponse finale : est-elle
FIDELE aux donnees renvoyees par les outils, et coherente avec la question ? On utilise
une sortie STRUCTUREE (JudgeVerdict) pour un verdict exploitable. Si le juge rejette,
l'agent corrige (boucle bornee dans graph.py) puis fallback.

POURQUOI un juge LLM (et non deterministe) : il evalue la coherence GLOBALE (pas seulement
l'annee) — realisateur, genre, identite du film, pertinence — ce qu'une regle figee ne peut
pas couvrir.
"""

from functools import lru_cache

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_ollama import ChatOllama
from pydantic import BaseModel, Field

from backend import trace
from backend.config import settings

FALLBACK_ANSWER = "Desole, je ne peux pas garantir cette information de maniere fiable."


class JudgeVerdict(BaseModel):
    valid: bool = Field(description="True si la reponse est fidele aux donnees des outils")
    reason: str = Field(description="Justification courte du verdict")


_JUDGE_SYSTEM = """\
Tu es un JUGE de fidelite. On te donne la QUESTION, les DONNEES renvoyees par des outils, et
la REPONSE de l'assistant. Tu verifies seulement que la REPONSE est FIDELE aux DONNEES.

REGLES ABSOLUES :
- N'utilise JAMAIS tes propres connaissances. Ne fais AUCUN calcul toi-meme (age, date, etc.).
- Une valeur PRESENTE dans les DONNEES est correcte PAR DEFINITION : si la reponse la reprend
  (ex. un age, une annee, un realisateur deja calcules/fournis), la reponse est VALIDE.
- Declare INVALIDE (valid=false) UNIQUEMENT si la reponse affirme un fait ABSENT des DONNEES,
  CONTREDIT directement une donnee, ou parle d'un AUTRE film que celui des DONNEES.
- Dans le doute, declare VALIDE (valid=true). Tolerant sur le style, strict sur l'invention.
Donne une raison courte.
"""


@lru_cache(maxsize=1)
def _judge_llm():
    """LLM du juge (sortie structuree), cree une seule fois."""
    return ChatOllama(
        model=settings.judge_model,
        base_url=settings.ollama_base_url,
        temperature=0,
    ).with_structured_output(JudgeVerdict)


def evaluate(question: str, answer: str, tool_outputs: list[str]) -> tuple[bool, str]:
    """Renvoie (valide, raison). Fail-open : si le juge echoue, on ne bloque pas le flux."""
    observations = "\n".join(tool_outputs) or "(aucune donnee d'outil)"
    user = (
        f"QUESTION:\n{question}\n\n"
        f"DONNEES DES OUTILS:\n{observations}\n\n"
        f"REPONSE A JUGER:\n{answer}"
    )
    try:
        verdict = _judge_llm().invoke(
            [SystemMessage(content=_JUDGE_SYSTEM), HumanMessage(content=user)]
        )
        label = "valide" if verdict.valid else "rejete"
        trace.record("judge", settings.judge_model, f"{label} — {verdict.reason}")
        return bool(verdict.valid), verdict.reason
    except Exception:  # noqa: BLE001 — le juge ne doit jamais casser l'agent
        trace.record("judge", "erreur", "juge indisponible (fail-open : on laisse passer)")
        return True, "juge indisponible"

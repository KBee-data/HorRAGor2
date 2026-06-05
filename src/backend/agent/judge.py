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

from backend.config import settings

FALLBACK_ANSWER = "Desole, je ne peux pas garantir cette information de maniere fiable."


class JudgeVerdict(BaseModel):
    valid: bool = Field(description="True si la reponse est fidele aux donnees des outils")
    reason: str = Field(description="Justification courte du verdict")


_JUDGE_SYSTEM = """\
Tu es un JUGE qualite pour un assistant specialise films d'horreur. On te donne la QUESTION
de l'utilisateur, les DONNEES factuelles renvoyees par des outils, et la REPONSE de l'assistant.

Declare la reponse INVALIDE (valid=false) si elle :
- affirme un fait (realisateur, annee, age, genre, titre) ABSENT des DONNEES ou contredit ;
- invente des informations non presentes dans les DONNEES ;
- est incoherente avec la QUESTION (ex. : parle d'un autre film que celui demande).
Sinon, declare-la VALIDE (valid=true). Sois STRICT sur les faits, tolerant sur le style.
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
        return bool(verdict.valid), verdict.reason
    except Exception:  # noqa: BLE001 — le juge ne doit jamais casser l'agent
        return True, "juge indisponible"

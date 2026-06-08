"""Boucle ReAct LangGraph + nœud Juge LLM.

Flux : Agent (LLM) -> [Tools <-> Agent]* -> Juge -> reponse validee | correction | fallback.
`AgentGraph` implemente `AgentEngine` (remplace le FakeEngine dans l'API) et expose, en plus
de la reponse, une **trace** des etapes (outils, juge) pour comprendre la mecanique interne.
"""

import asyncio
import logging
from functools import lru_cache

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage
from langchain_ollama import ChatOllama
from langgraph.errors import GraphRecursionError
from langgraph.graph import END, START, StateGraph
from langgraph.prebuilt import ToolNode

from backend import trace
from backend.agent import judge
from backend.agent.prompts import SYSTEM_PROMPT
from backend.agent.state import AgentState
from backend.agent.tools_registry import TOOLS
from backend.config import settings
from backend.contracts.schemas import ChatRequest, ChatResponse

logger = logging.getLogger("horragor")

MAX_RETRIES = 2
RECURSION_LIMIT = 25  # nb max de "super-pas" du graphe avant abandon


def _as_text(content) -> str:
    """Le contenu d'un message peut etre une chaine ou une liste de blocs -> on normalise."""
    if isinstance(content, list):
        return " ".join(
            part.get("text", "") if isinstance(part, dict) else str(part) for part in content
        ).strip()
    return content or ""


@lru_cache(maxsize=1)
def _llm():
    """LLM Ollama lie aux outils (cree une seule fois)."""
    return ChatOllama(
        model=settings.llm_model,
        base_url=settings.ollama_base_url,
        temperature=0,  # deterministe : on veut des reponses factuelles stables
    ).bind_tools(TOOLS)


def _agent_node(state: AgentState) -> dict:
    """Noeud "cerveau" : le LLM raisonne et decide d'appeler un outil ou de repondre."""
    messages = [SystemMessage(content=SYSTEM_PROMPT), *state["messages"]]
    return {"messages": [_llm().invoke(messages)]}


def _route_from_agent(state: AgentState) -> str:
    """Si le dernier message contient des tool_calls -> Tools, sinon -> Juge."""
    last = state["messages"][-1]
    return "tools" if getattr(last, "tool_calls", None) else "judge"


def _original_question(messages) -> str:
    """Le premier message humain = la question de l'utilisateur (≠ messages de correction)."""
    for m in messages:
        if isinstance(m, HumanMessage):
            return _as_text(m.content)
    return ""


def _judge_node(state: AgentState) -> dict:
    """Audit par le Juge LLM (cf. judge.evaluate)."""
    messages = state["messages"]
    answer = _as_text(messages[-1].content)
    tool_outputs = [str(m.content) for m in messages if isinstance(m, ToolMessage)]

    valid, reason = judge.evaluate(_original_question(messages), answer, tool_outputs)
    if valid:
        return {"verdict": "valid"}

    retries = state.get("retries", 0)
    if retries >= MAX_RETRIES:
        # Corrections epuisees : on substitue une reponse honnete.
        return {"verdict": "fallback", "messages": [AIMessage(content=judge.FALLBACK_ANSWER)]}

    correction = HumanMessage(
        content=(
            f"Un juge a rejete ta reponse (raison : {reason}). Corrige en t'appuyant "
            "UNIQUEMENT sur les donnees des outils, ou dis que tu ne sais pas."
        )
    )
    return {"verdict": "retry", "messages": [correction], "retries": retries + 1}


def _route_from_judge(state: AgentState) -> str:
    """Verdict 'retry' -> retour a l'agent ; sinon (valid/fallback) -> fin."""
    return "agent" if state.get("verdict") == "retry" else END


def build_graph():
    """Compile le graphe ReAct + Juge."""
    graph = StateGraph(AgentState)
    graph.add_node("agent", _agent_node)
    graph.add_node("tools", ToolNode(TOOLS))
    graph.add_node("judge", _judge_node)

    graph.add_edge(START, "agent")
    graph.add_conditional_edges("agent", _route_from_agent, {"tools": "tools", "judge": "judge"})
    graph.add_edge("tools", "agent")
    graph.add_conditional_edges("judge", _route_from_judge, {"agent": "agent", END: END})
    return graph.compile()


def _sources(state: AgentState) -> list[str]:
    """Tracabilite : les outils reellement appeles pendant le parcours."""
    names = [
        tc["name"]
        for m in state["messages"]
        for tc in (getattr(m, "tool_calls", None) or [])
    ]
    return sorted(set(names))


class AgentGraph:
    """Implemente `contracts.interfaces.AgentEngine` en enveloppant le graphe ReAct + Juge."""

    def __init__(self):
        self._graph = build_graph()

    async def run(self, req: ChatRequest) -> ChatResponse:
        # Le graphe (LLM Ollama + tools) est synchrone et bloquant : on l'execute dans un
        # thread pour NE PAS geler la boucle d'evenements de l'API (critere "pas de gel").
        # On capture TOUTE erreur : l'API ne doit jamais renvoyer un 500 a cause de l'agent.
        events = trace.begin()  # collecteur de la trace fine (se propage au thread)
        try:
            state = await asyncio.to_thread(
                self._graph.invoke,
                {"messages": [HumanMessage(content=req.message)], "retries": 0},
                {"recursion_limit": RECURSION_LIMIT},
            )
        except GraphRecursionError:
            # Le petit modele a boucle sans converger.
            logger.warning("Agent : limite de recursion atteinte pour: %r", req.message)
            return ChatResponse(
                answer="Desole, je n'ai pas reussi a traiter cette demande. Peux-tu la reformuler "
                "plus simplement (par exemple en citant un seul film) ?",
                sources=[],
                verdict="error",
            )
        except Exception:
            logger.exception("Agent : erreur inattendue pour: %r", req.message)
            return ChatResponse(
                answer="Une erreur interne est survenue. Reessaie dans un instant.",
                sources=[],
                verdict="error",
            )

        trace.record("verdict", state.get("verdict") or "valid")
        response = ChatResponse(
            answer=_as_text(state["messages"][-1].content) or "(reponse vide)",
            sources=_sources(state),
            verdict=state.get("verdict"),
            trace=events,
        )
        trace.log_trace(req.message, response)  # persistance best-effort (logs/, gitignore)
        return response

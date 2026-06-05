"""Boucle ReAct LangGraph + nœud Juge deterministe.

Flux : Agent (LLM) -> [Tools <-> Agent]* -> Juge -> reponse validee | correction | fallback.
`AgentGraph` (etape 4) enveloppera ce graphe pour implementer `AgentEngine` et remplacer
le FakeEngine dans l'API, sans rien changer au contrat.
"""

from functools import lru_cache

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage
from langchain_ollama import ChatOllama
from langgraph.graph import END, START, StateGraph
from langgraph.prebuilt import ToolNode

from backend.agent import judge
from backend.agent.prompts import SYSTEM_PROMPT
from backend.agent.state import AgentState
from backend.agent.tools_registry import TOOLS
from backend.config import settings

MAX_RETRIES = 2


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


def _judge_node(state: AgentState) -> dict:
    """Audit deterministe de la reponse finale (cf. judge.verify)."""
    messages = state["messages"]
    answer = messages[-1].content or ""
    tool_outputs = [str(m.content) for m in messages if isinstance(m, ToolMessage)]

    if judge.verify(answer, tool_outputs):
        return {"verdict": "valid"}

    retries = state.get("retries", 0)
    if retries >= MAX_RETRIES:
        # Corrections epuisees : on substitue une reponse honnete.
        return {"verdict": "fallback", "messages": [AIMessage(content=judge.FALLBACK_ANSWER)]}

    correction = HumanMessage(
        content=(
            "Ta reponse cite une annee absente des donnees des outils. Reprends en "
            "utilisant UNIQUEMENT les valeurs renvoyees par les outils, ou dis que tu ne sais pas."
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

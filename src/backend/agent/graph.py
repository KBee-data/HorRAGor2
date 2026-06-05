"""Boucle ReAct LangGraph.

Flux : Agent (LLM) -> [Tools <-> Agent]* -> (Juge, etape 3) -> reponse | fallback.
`AgentGraph` (etape 4) enveloppera ce graphe pour implementer `AgentEngine` et remplacer
le FakeEngine dans l'API, sans rien changer au contrat.
"""

from functools import lru_cache

from langchain_core.messages import SystemMessage
from langchain_ollama import ChatOllama
from langgraph.graph import END, START, StateGraph
from langgraph.prebuilt import ToolNode

from backend.agent.prompts import SYSTEM_PROMPT
from backend.agent.state import AgentState
from backend.agent.tools_registry import TOOLS
from backend.config import settings


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


def _should_continue(state: AgentState) -> str:
    """Routage : si le dernier message contient des tool_calls -> Tools, sinon -> fin."""
    last = state["messages"][-1]
    return "tools" if getattr(last, "tool_calls", None) else END


def build_graph():
    """Compile le graphe ReAct (agent <-> tools)."""
    graph = StateGraph(AgentState)
    graph.add_node("agent", _agent_node)
    graph.add_node("tools", ToolNode(TOOLS))
    graph.add_edge(START, "agent")
    graph.add_conditional_edges("agent", _should_continue, {"tools": "tools", END: END})
    graph.add_edge("tools", "agent")
    return graph.compile()

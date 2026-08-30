"""Streamlit Frontend for HorRAGor Part 3: Distributed Multi-Agent Architecture.

Features:
- Atmospheric dark/gothic horror UI theme.
- Asynchronous communication with the FastAPI backend (/chat).
- Source attribution badges (FAISS, Local DB, Wikipedia).
- Context Trimming & Agent Reasoning expanders to inspect multi-agent cooperation.
"""

import httpx
import streamlit as st

st.set_page_config(
    page_title="HorRAGor3 — The Gothic Storyteller 👻",
    page_icon="👻",
    layout="wide",
)

API_URL = "http://127.0.0.1:8000/chat"

# --- Source Badge Styling ---
SOURCE_ICONS = {
    "FAISS Vector Index": "🔎 FAISS Vector Index",
    "Local Horror DB": "🗄️ Local DB (SQL)",
    "Wikipedia Web Scraper": "🌐 Wikipedia Web Scraper",
}


def _render_meta(msg: dict) -> None:
    """Renders sources used during the multi-agent execution."""
    sources = msg.get("sources") or []
    if sources:
        badges = [SOURCE_ICONS.get(s, f"📌 {s}") for s in sources]
        st.caption(" · ".join(badges))


def _render_context_inspector(msg: dict) -> None:
    """Expander showing context trimming and isolated facts fed to the Gothic Writer."""
    summary = msg.get("context_summary")
    title = msg.get("extracted_title")
    if not summary:
        return

    with st.expander("🔍 Multi-Agent Behind-the-Scenes: Context Trimming & Isolated Facts"):
        if title:
            st.markdown(f"**Canonical Title (FAISS Match)**: `{title}`")
        st.markdown("**Clean Factual Synthesis Transmitted to Narration Agent (Token Isolation):**")
        st.code(summary, language="text")


# --- Sidebar ---
with st.sidebar:
    st.header("HorRAGor Part 3 👻")
    st.caption("Distributed Multi-Agent Architecture with LangGraph.")
    st.markdown("---")
    st.markdown("**Specialized Agents:**")
    st.markdown("1. 🔎 **RAG Agent** *(Local Researcher: FAISS & SQL)*")
    st.markdown("2. 🌐 **Scraper Agent** *(Web Investigator: Wikipedia)*")
    st.markdown("3. 🖋️ **Narration Agent** *(Gothic Writer: Pure Prose)*")
    st.markdown("---")
    if st.button("🗑️ New Conversation", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

    st.markdown("**Example Questions / Exemples :**")
    st.markdown(
        "- *Who directed The Thing and what is the story about?*\n"
        "- *Quels sont les films similaires à Hereditary ?*\n"
        "- *Tell me some trivia about the 1979 film Alien.*"
    )

# --- Main Chat Area ---
st.title("HorRAGor3: The Gothic Storyteller 👻")
st.caption("Inquire into the terrifying archives of horror cinema...")

if "messages" not in st.session_state:
    st.session_state.messages = []

# Display conversation history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if msg["role"] == "assistant":
            _render_meta(msg)
            _render_context_inspector(msg)

# User Chat Input
if prompt := st.chat_input("Ask a question about a horror movie (English or French)..."):
    # 1. User Message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # 2. Assistant Response
    with st.chat_message("assistant"):
        with st.spinner("The dark entities are stirring (RAG → Scraper → Narration)..."):
            try:
                resp = httpx.post(API_URL, json={"message": prompt}, timeout=120.0)
                if resp.status_code == 200:
                    data = resp.json()
                    entry = {
                        "role": "assistant",
                        "content": data.get("answer", "Empty response."),
                        "sources": data.get("sources", []),
                        "extracted_title": data.get("extracted_title"),
                        "context_summary": data.get("context_summary"),
                    }
                else:
                    entry = {
                        "role": "assistant",
                        "content": f"⚠️ API Error ({resp.status_code}): {resp.text}",
                        "sources": [],
                        "extracted_title": None,
                        "context_summary": None,
                    }
            except Exception as exc:
                entry = {
                    "role": "assistant",
                    "content": f"⚠️ Unable to reach HorRAGor API: {exc}",
                    "sources": [],
                    "extracted_title": None,
                    "context_summary": None,
                }

        st.markdown(entry["content"])
        _render_meta(entry)
        _render_context_inspector(entry)

    st.session_state.messages.append(entry)

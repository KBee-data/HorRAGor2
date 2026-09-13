"""Streamlit Frontend for HorRAGor Part 3 & 4: Multi-Agent Architecture with OAuth2 & JWT Security.

Features:
- Atmospheric dark/gothic horror UI theme.
- OAuth2 Password Bearer authentication & Registration interface.
- RS256 JWT Access & Refresh token session management.
- Protected asynchronous communication with the FastAPI backend (/chat).
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

API_BASE = "http://127.0.0.1:8000"
API_CHAT_URL = f"{API_BASE}/chat"
API_LOGIN_URL = f"{API_BASE}/auth/login"
API_REGISTER_URL = f"{API_BASE}/auth/register"
API_REFRESH_URL = f"{API_BASE}/auth/refresh"

# --- Initialize Session State ---
if "access_token" not in st.session_state:
    st.session_state.access_token = None
if "refresh_token" not in st.session_state:
    st.session_state.refresh_token = None
if "user" not in st.session_state:
    st.session_state.user = None
if "messages" not in st.session_state:
    st.session_state.messages = []
if "active_title" not in st.session_state:
    st.session_state.active_title = None

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


# --- Authentication Actions ---
def login_user(username: str, password: str) -> None:
    """Logs in the user and saves JWT tokens in session state."""
    try:
        resp = httpx.post(
            API_LOGIN_URL,
            data={"username": username, "password": password},
            timeout=10.0,
        )
        if resp.status_code == 200:
            data = resp.json()
            st.session_state.access_token = data["access_token"]
            st.session_state.refresh_token = data["refresh_token"]
            st.session_state.user = data["user"]
            st.rerun()
        else:
            st.error(f"Authentication failed: {resp.json().get('detail', 'Invalid credentials')}")
    except Exception as exc:
        st.error(f"Unable to reach authentication server: {exc}")


def register_user(username: str, email: str, password: str) -> None:
    """Registers a new user account."""
    try:
        resp = httpx.post(
            API_REGISTER_URL,
            json={"username": username, "email": email, "password": password},
            timeout=10.0,
        )
        if resp.status_code == 201:
            st.success("Account created successfully! You can now log in.")
        else:
            st.error(f"Registration failed: {resp.json().get('detail', 'Error')}")
    except Exception as exc:
        st.error(f"Unable to reach authentication server: {exc}")


def logout_user() -> None:
    """Clears authentication and conversation state."""
    st.session_state.access_token = None
    st.session_state.refresh_token = None
    st.session_state.user = None
    st.session_state.messages = []
    st.session_state.active_title = None
    st.rerun()


# ==============================================================================
# VIEW 1: Unauthenticated View (Login & Registration Forms)
# ==============================================================================
if not st.session_state.access_token:
    st.title("HorRAGor3: The Gothic Storyteller 👻")
    st.caption("Enter your credentials to unlock the cursed archives of horror cinema.")

    tab_login, tab_register = st.tabs(["🔐 Log In", "📝 Create Account"])

    with tab_login:
        with st.form("login_form"):
            l_username = st.text_input("Username or Email")
            l_password = st.text_input("Password", type="password")
            submitted = st.form_submit_button("Enter the Shadows (Log In)", use_container_width=True)
            if submitted:
                if l_username and l_password:
                    login_user(l_username, l_password)
                else:
                    st.warning("Please enter your username and password.")

    with tab_register:
        with st.form("register_form"):
            r_username = st.text_input("Choose a Username (min 3 chars)")
            r_email = st.text_input("Email Address")
            r_password = st.text_input("Choose a Password (min 6 chars)", type="password")
            submitted = st.form_submit_button("Join the Coven (Register)", use_container_width=True)
            if submitted:
                if len(r_username) >= 3 and r_email and len(r_password) >= 6:
                    register_user(r_username, r_email, r_password)
                else:
                    st.warning("Please complete all fields (username ≥ 3 chars, password ≥ 6 chars).")

    st.stop()


# ==============================================================================
# VIEW 2: Authenticated View (Multi-Agent Gothic Storyteller)
# ==============================================================================
with st.sidebar:
    st.header(f"👻 Welcome, {st.session_state.user.get('username') if st.session_state.user else 'Traveler'}")
    st.caption("🔒 Secured via OAuth2 / RS256 JWT")
    if st.button("🚪 Log Out", use_container_width=True):
        logout_user()

    st.markdown("---")
    st.markdown("**Specialized Agents:**")
    st.markdown("1. 🔎 **RAG Agent** *(Local Researcher: FAISS & SQL)*")
    st.markdown("2. 🌐 **Scraper Agent** *(Web Investigator: Wikipedia)*")
    st.markdown("3. 🖋️ **Narration Agent** *(Gothic Writer: Pure Prose)*")
    st.markdown("---")
    if st.button("🗑️ New Conversation", use_container_width=True):
        st.session_state.messages = []
        st.session_state.active_title = None
        st.rerun()

    st.markdown("**Example Questions / Exemples :**")
    st.markdown(
        "- *Who directed The Thing?*\n"
        "- *What year was it released? (Follow-up)*\n"
        "- *Quels sont les films similaires à Hereditary ?*"
    )

# --- Main Chat Area ---
st.title("HorRAGor3: The Gothic Storyteller 👻")
st.caption("Inquire into the terrifying archives of horror cinema...")

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
                headers = {"Authorization": f"Bearer {st.session_state.access_token}"}
                payload = {
                    "message": prompt,
                    "history": [{"role": m["role"], "content": m["content"]} for m in st.session_state.messages[:-1]],
                    "active_title": st.session_state.get("active_title"),
                }
                resp = httpx.post(API_CHAT_URL, json=payload, headers=headers, timeout=120.0)

                # Token expired -> try silent refresh
                if resp.status_code == 401 and st.session_state.refresh_token:
                    ref_resp = httpx.post(
                        API_REFRESH_URL,
                        json={"refresh_token": st.session_state.refresh_token},
                        timeout=10.0,
                    )
                    if ref_resp.status_code == 200:
                        st.session_state.access_token = ref_resp.json()["access_token"]
                        headers = {"Authorization": f"Bearer {st.session_state.access_token}"}
                        resp = httpx.post(API_CHAT_URL, json=payload, headers=headers, timeout=120.0)

                if resp.status_code == 200:
                    data = resp.json()
                    if data.get("active_title") or data.get("extracted_title"):
                        st.session_state.active_title = data.get("active_title") or data.get("extracted_title")

                    entry = {
                        "role": "assistant",
                        "content": data.get("answer", "Empty response."),
                        "sources": data.get("sources", []),
                        "extracted_title": data.get("extracted_title") or st.session_state.active_title,
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

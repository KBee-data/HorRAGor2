"""Interface de chat Streamlit.

Lancement (depuis la racine du projet, pour que .streamlit/config.toml soit pris) :
    uv run streamlit run src/front/streamlit/app.py

Exigences du PDF respectees :
- Composants de chat dedies : st.chat_input + st.chat_message (bulles + historique) ;
- Indicateur d'activite : st.spinner pendant la "reflexion" (evite les doubles envois) ;
- Decouplage strict : aucune logique LLM/Supabase ; uniquement un appel HTTP a l'API.

Le dialogue avec l'API vit dans front.common.api_client (partage, reutilisable par
un autre front).
"""

import streamlit as st

from front.common.api_client import send_message

st.set_page_config(page_title="HorRAGor2 👻", page_icon="👻")

# Libelles "humains" pour le verdict du Juge.
_VERDICT_BADGES = {
    "valid": "✅ validé",
    "fallback": "⚠️ non garanti",
    "mock": "🧪 mock",
}


def _render_meta(msg: dict) -> None:
    """Affiche, sous une reponse de l'assistant, le verdict du Juge et les outils utilises."""
    bits = []
    if verdict := msg.get("verdict"):
        bits.append(_VERDICT_BADGES.get(verdict, verdict))
    if sources := msg.get("sources"):
        bits.append("outils : " + ", ".join(sources))
    if bits:
        st.caption(" · ".join(bits))


# --- Barre laterale ---
with st.sidebar:
    st.header("HorRAGor2 👻")
    st.caption("Agent conversationnel spécialisé films d'horreur (RAG + LangGraph).")
    if st.button("🗑️ Nouvelle conversation", use_container_width=True):
        st.session_state.messages = []
        st.rerun()
    st.markdown("**Exemples de questions :**")
    st.markdown(
        "- Qui a réalisé The Thing ?\n"
        "- Des films similaires à Hereditary ?\n"
        "- Quel âge a le film Alien ?"
    )

st.title("L'Agent de l'Horreur 👻")

# POURQUOI st.session_state : Streamlit re-execute tout le script a chaque interaction.
# session_state persiste l'historique entre ces re-executions (sinon il serait perdu).
if "messages" not in st.session_state:
    st.session_state.messages = []

# Re-affiche tout l'historique sous forme de bulles a chaque rendu.
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if msg["role"] == "assistant":
            _render_meta(msg)

# st.chat_input : champ de saisie dedie, ancre en bas de page.
if prompt := st.chat_input("Pose ta question sur un film d'horreur..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        # st.spinner : loader visuel pendant l'attente -> experience fluide,
        # et l'input est desactive le temps de la reponse (pas de double soumission).
        with st.spinner("Réflexion..."):
            try:
                response = send_message(prompt)
                entry = {
                    "role": "assistant",
                    "content": response.answer,
                    "sources": response.sources,
                    "verdict": response.verdict,
                }
            except Exception as exc:  # noqa: BLE001 — on affiche toute erreur a l'utilisateur
                entry = {
                    "role": "assistant",
                    "content": f"⚠️ Erreur de connexion à l'API : {exc}",
                    "sources": [],
                    "verdict": None,
                }
        st.markdown(entry["content"])
        _render_meta(entry)

    st.session_state.messages.append(entry)

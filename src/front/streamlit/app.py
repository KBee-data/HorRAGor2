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
st.title("HorRAGor2 — L'Agent de l'Horreur 👻")

# POURQUOI st.session_state : Streamlit re-execute tout le script a chaque interaction.
# session_state persiste l'historique entre ces re-executions (sinon il serait perdu).
if "messages" not in st.session_state:
    st.session_state.messages = []

# Re-affiche tout l'historique sous forme de bulles a chaque rendu.
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# st.chat_input : champ de saisie dedie, ancre en bas de page.
if prompt := st.chat_input("Pose ta question sur un film d'horreur..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        # st.spinner : loader visuel pendant l'attente -> experience fluide,
        # et l'input est desactive le temps de la reponse (pas de double soumission).
        with st.spinner("Reflexion..."):
            try:
                response = send_message(prompt)
                answer = response.answer
                if response.sources:
                    answer += f"\n\n_Sources : {', '.join(response.sources)}_"
            except Exception as exc:  # noqa: BLE001 — on affiche toute erreur a l'utilisateur
                answer = f"⚠️ Erreur de connexion a l'API : {exc}"
        st.markdown(answer)

    st.session_state.messages.append({"role": "assistant", "content": answer})

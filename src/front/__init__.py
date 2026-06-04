"""Front-End HorRAGor2 (responsable : A).

Organise par techno pour pouvoir ajouter d'autres fronts a l'avenir (le PDF autorise
Streamlit OU Gradio) :
- `common/`    : code reutilisable par TOUS les fronts (client HTTP vers l'API) ;
- `streamlit/` : le front Streamlit concret.
  (futur : `gradio/` reutiliserait `front.common`.)

Decouplage strict (PDF) : aucune logique metier ici, uniquement la capture de la
question, l'appel HTTP a l'API et l'affichage de la reponse JSON.
"""

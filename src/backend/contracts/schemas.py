"""Forme des donnees echangees (modeles Pydantic).

POURQUOI Pydantic (exige par le PDF, "Typage strict") :
- valide et serialise automatiquement les requetes entrantes et reponses sortantes ;
- documente l'API (FastAPI genere le schema OpenAPI a partir de ces classes) ;
- garantit que le Front et l'API parlent exactement la meme structure JSON.

⚠️ Schemas partages : ne pas modifier sans prevenir l'equipe.
"""

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    """Ce que le Front envoie a l'API (POST /chat)."""

    message: str
    # session_id : permet plus tard de relier les messages d'une meme conversation.
    session_id: str = "default"


class FilmRef(BaseModel):
    """Reference minimale d'un film (sortie du routeur FAISS ou d'une reco)."""

    id: int
    title: str


class FilmMetadata(BaseModel):
    """Metadonnees completes (renvoyees par le connecteur SQL securise).

    Champs alignes sur le PDF (Tool 1) : realisateur, annee, genre,
    note moyenne, casting. Tous optionnels pour rester tolerant aux donnees
    incompletes du golden data.
    """

    id: int
    title: str
    tmdb_id: int | None = None  # identifiant TMDB (sert a enrichir realisateur/casting)
    director: str | None = None  # absent de la base -> enrichi via TMDB
    release_year: int | None = None  # derive de movies.release_date
    genres: list[str] = Field(default_factory=list)  # jointure movie_genres (multi-genres)
    rating: float | None = None  # note 0-10 (imdb/tmdb) issue de la table ratings
    cast: list[str] = Field(default_factory=list)  # casting -> enrichi via TMDB
    synopsis: str | None = None  # movies.overview


class ChatResponse(BaseModel):
    """Ce que l'API renvoie au Front.

    `sources` rend la reponse tracable (anti-hallucination) ; `verdict` expose
    le resultat du nœud Juge (valide / corrige / fallback) pour la transparence.
    """

    answer: str
    sources: list[str] = Field(default_factory=list)
    verdict: str | None = None

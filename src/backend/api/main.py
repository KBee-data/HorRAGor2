"""Point d'entree de l'API FastAPI.

Lancement :
    uv run horragor-api        (raccourci)
    uv run uvicorn backend.api.main:app --reload
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.api.routes import router
from backend.config import settings
from backend.data.faiss_index import TitleIndex
from backend.tools.faiss_tool import set_index

logger = logging.getLogger("horragor")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Charge l'index FAISS UNE fois au demarrage -> routage instantane (en RAM).

    Degradation propre : si l'index n'a pas encore ete construit, l'API demarre
    quand meme (health, chat mocke...) ; seul `validate_film` sera indisponible.
    """
    if TitleIndex.exists():
        index = TitleIndex.load()
        set_index(index)
        logger.info("Index FAISS charge : %d titres en RAM.", len(index))
    else:
        logger.warning(
            "Index FAISS absent (%s). Lancez `uv run horragor-faiss` pour le construire ; "
            "validate_film sera indisponible d'ici la.",
            settings.faiss_index_dir,
        )
    yield


app = FastAPI(title="HorRAGor2 API", version="0.1.0", lifespan=lifespan)

# POURQUOI CORS : le Front Streamlit s'execute sur une autre origine (autre port).
# Sans cette autorisation, le navigateur bloquerait les appels du Front vers l'API.
# (En production, restreindre `allow_origins` a l'URL reelle du Front.)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)


def run() -> None:
    """Demarre le serveur (cible du script `horragor-api`).

    On passe l'app en chaine d'import "backend.api.main:app" pour que `reload=True`
    puisse recharger le module a chaud lors des modifications.
    """
    import uvicorn

    uvicorn.run(
        "backend.api.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=True,
    )

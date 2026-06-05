"""Calcul des embeddings via Ollama (local).

POURQUOI un module unique : le modele d'embeddings (settings.embedding_model) doit
etre le MEME a la construction de l'index ET a la requete, sinon les similarites
cosinus n'ont aucun sens. Centraliser ici garantit cette coherence. Ce helper sert
a la fois au routeur FAISS (titres) et, plus tard, a la reco pgvector (synopsis).

Ollama expose deux endpoints d'embeddings :
- `/api/embed`      : moderne, accepte un BATCH (`input`: liste) -> `{"embeddings": [[...]]}` ;
- `/api/embeddings` : legacy, un seul texte (`prompt`) -> `{"embedding": [...]}`.
On utilise le batch (rapide pour des milliers de titres) avec repli sur le legacy.
"""

import httpx

from backend.config import settings


def embed_texts(texts: list[str]) -> list[list[float]]:
    """Renvoie un vecteur par texte (ordre preserve). Liste vide -> liste vide."""
    if not texts:
        return []

    vectors = _embed_batch(texts)

    # Garde-fou : la dimension renvoyee doit matcher la config (et donc l'index /
    # la colonne pgvector). Une incoherence ici casserait silencieusement la reco.
    if vectors and len(vectors[0]) != settings.embedding_dim:
        raise ValueError(
            f"Dimension d'embedding inattendue : {len(vectors[0])} "
            f"(attendu {settings.embedding_dim} pour '{settings.embedding_model}')."
        )
    return vectors


def embed_text(text: str) -> list[float]:
    """Embedde un seul texte (raccourci pour les requetes unitaires)."""
    return embed_texts([text])[0]


def _embed_batch(texts: list[str]) -> list[list[float]]:
    """Appel Ollama `/api/embed` (batch), avec repli sur le legacy `/api/embeddings`."""
    url = f"{settings.ollama_base_url}/api/embed"
    resp = httpx.post(
        url,
        json={"model": settings.embedding_model, "input": texts},
        timeout=300,  # large : un gros batch sur CPU peut etre long
    )
    if resp.status_code == 404:
        # Instance Ollama ancienne : on retombe sur l'endpoint legacy (1 par 1).
        return [_embed_legacy(t) for t in texts]
    resp.raise_for_status()
    embeddings = resp.json().get("embeddings")
    if embeddings is None:
        raise RuntimeError(f"Reponse Ollama inattendue (pas de 'embeddings') : {resp.text[:200]}")
    return embeddings


def _embed_legacy(text: str) -> list[float]:
    resp = httpx.post(
        f"{settings.ollama_base_url}/api/embeddings",
        json={"model": settings.embedding_model, "prompt": text},
        timeout=300,
    )
    resp.raise_for_status()
    return resp.json()["embedding"]

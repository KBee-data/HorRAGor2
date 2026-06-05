"""Verifie que l'API demarre (lifespan) que l'index FAISS soit present ou non."""

from fastapi.testclient import TestClient

from backend.api.main import app


def test_app_starts_and_health_ok():
    # Le bloc `with` declenche le lifespan (chargement de l'index si present,
    # avertissement sinon) : dans les deux cas le demarrage ne doit pas planter.
    with TestClient(app) as client:
        resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}

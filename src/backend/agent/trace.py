"""Persistance des traces d'execution de l'agent (JSONL, dossier `logs/` gitignore).

POURQUOI : garder une trace a posteriori (debug / analyse) sans polluer le depot.
Best-effort : ecrire une trace ne doit JAMAIS casser une reponse.
"""

import json
from datetime import UTC, datetime

from backend.config import _PROJECT_ROOT
from backend.contracts.schemas import ChatResponse

_LOG_PATH = _PROJECT_ROOT / "logs" / "traces.jsonl"


def log_trace(question: str, response: ChatResponse) -> None:
    """Ajoute une ligne JSON (un run) dans logs/traces.jsonl."""
    try:
        _LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        record = {
            "ts": datetime.now(UTC).isoformat(),
            "question": question,
            "answer": response.answer,
            "verdict": response.verdict,
            "sources": response.sources,
            "trace": [step.model_dump() for step in response.trace],
        }
        with _LOG_PATH.open("a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
    except Exception:  # noqa: BLE001 — le logging ne doit jamais casser la reponse
        pass

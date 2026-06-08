"""Trace FINE du raisonnement de l'agent — on veut tout voir (projet d'apprentissage).

Mecanisme : un `ContextVar` porte la liste d'evenements du run courant. N'importe quelle
fonction profonde (outil, FAISS, SQL, TMDB, pgvector, Wikipedia, juge...) appelle
`record(...)` pour s'y ajouter — sans avoir a faire transiter un logger dans toutes les
signatures, et sans couplage (ce module ne depend que de config + contracts).

`asyncio.to_thread` (utilise par l'agent) PROPAGE le contexte au thread : les sous-appels
executes dans le thread sont donc bien captures dans la meme liste.
"""

import contextvars
import json
from datetime import UTC, datetime

from backend.config import _PROJECT_ROOT
from backend.contracts.schemas import ChatResponse, TraceStep

_events: contextvars.ContextVar[list[TraceStep] | None] = contextvars.ContextVar(
    "trace_events", default=None
)
_LOG_PATH = _PROJECT_ROOT / "logs" / "traces.jsonl"


def begin() -> list[TraceStep]:
    """Demarre une nouvelle trace (debut d'un run). Renvoie la liste collectrice."""
    events: list[TraceStep] = []
    _events.set(events)
    return events


def record(kind: str, name: str, detail: str = "") -> None:
    """Ajoute une etape a la trace courante. No-op hors d'un run (ex. scripts offline)."""
    events = _events.get()
    if events is not None:
        events.append(TraceStep(kind=kind, name=name, detail=str(detail)[:300]))


def log_trace(question: str, response: ChatResponse) -> None:
    """Persiste un run (1 ligne JSON) dans logs/traces.jsonl. Best-effort."""
    try:
        _LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        record_obj = {
            "ts": datetime.now(UTC).isoformat(),
            "question": question,
            "answer": response.answer,
            "verdict": response.verdict,
            "sources": response.sources,
            "trace": [step.model_dump() for step in response.trace],
        }
        with _LOG_PATH.open("a", encoding="utf-8") as f:
            f.write(json.dumps(record_obj, ensure_ascii=False) + "\n")
    except Exception:  # noqa: BLE001 — le logging ne doit jamais casser la reponse
        pass

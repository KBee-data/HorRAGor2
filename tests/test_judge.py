"""Tests du Juge LLM — le modele est MOQUE (pas d'appel Ollama)."""

from backend.agent import judge
from backend.agent.judge import JudgeVerdict


def _patch_judge(monkeypatch, verdict: JudgeVerdict | None = None, boom: bool = False):
    class _Fake:
        def invoke(self, messages):
            if boom:
                raise RuntimeError("juge indisponible")
            return verdict

    monkeypatch.setattr(judge, "_judge_llm", lambda: _Fake())


def test_evaluate_valid(monkeypatch):
    _patch_judge(monkeypatch, JudgeVerdict(valid=True, reason="fidele aux donnees"))
    ok, reason = judge.evaluate("Qui a realise X ?", "Reponse", ["{'director': 'Y'}"])
    assert ok is True
    assert "fidele" in reason


def test_evaluate_invalid(monkeypatch):
    _patch_judge(monkeypatch, JudgeVerdict(valid=False, reason="annee inventee"))
    ok, reason = judge.evaluate("q", "reponse douteuse", [])
    assert ok is False
    assert "inventee" in reason


def test_evaluate_fail_open_on_error(monkeypatch):
    # Si le juge tombe en erreur, on ne bloque pas le flux (fail-open).
    _patch_judge(monkeypatch, boom=True)
    ok, _ = judge.evaluate("q", "a", [])
    assert ok is True

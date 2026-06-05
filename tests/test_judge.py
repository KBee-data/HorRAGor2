"""Tests du Juge deterministe (verification d'ancrage des annees)."""

from backend.agent.judge import verify


def test_year_grounded_passes():
    assert verify("Le film est sorti en 1982.", ["{'release_year': 1982}"]) is True


def test_year_not_grounded_fails():
    assert verify("Le film est sorti en 1999.", ["{'release_year': 1982}"]) is False


def test_no_year_passes():
    assert verify("Realise par John Carpenter.", ["peu importe"]) is True


def test_all_cited_years_must_be_observed():
    assert verify("Entre 1979 et 1982.", ["1979", "1982"]) is True
    assert verify("En 2050.", ["1979 1982"]) is False

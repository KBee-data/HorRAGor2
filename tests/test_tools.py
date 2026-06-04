"""Tests des tools deja implementables (calcul deterministe)."""

import pytest

from backend.tools.temporal_tool import calculate_movie_age


def test_calculate_movie_age_nominal():
    # On injecte l'annee courante pour un test deterministe.
    assert calculate_movie_age(1982, current_year=2025) == 43


def test_calculate_movie_age_future_raises():
    with pytest.raises(ValueError):
        calculate_movie_age(2999, current_year=2025)

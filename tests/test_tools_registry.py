"""Le registre expose bien les outils attendus par l'agent."""

from backend.agent.tools_registry import TOOLS


def test_registry_exposes_expected_tools():
    names = {t.name for t in TOOLS}
    assert names == {"lookup_movie", "find_similar", "movie_age", "wikipedia_synopsis"}


def test_tools_have_descriptions():
    # Les descriptions guident le LLM : aucune ne doit etre vide.
    assert all(t.description for t in TOOLS)

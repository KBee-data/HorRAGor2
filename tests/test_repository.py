"""Test du connecteur SQL sur un SQLite local (schema identique a Part 1, CI-safe)."""

from sqlalchemy import create_engine, text

from backend.data.repository import SupabaseFilmRepository


def _seeded_engine(tmp_path):
    # SQLite sur fichier : les tables sont partagees entre connexions (≠ in-memory).
    engine = create_engine(f"sqlite:///{tmp_path}/test.db")
    with engine.begin() as c:
        c.execute(text("create table movies (id integer primary key, title text, "
                       "release_date text, overview text)"))
        c.execute(text("create table genres (id integer primary key, name text)"))
        c.execute(text("create table movie_genres (movie_id integer, genre_id integer)"))
        c.execute(text("create table ratings (movie_id integer, source text, "
                       "score real, vote_count integer)"))
        c.execute(text("insert into movies values "
                       "(41,'Hereditary','2018-06-07','Une famille hantee...')"))
        c.execute(text("insert into genres values (1,'Horror'),(2,'Drama')"))
        c.execute(text("insert into movie_genres values (41,1),(41,2)"))
        c.execute(text("insert into ratings values "
                       "(41,'imdb',7.3,453938),(41,'rotten_tomatoes',90.0,null)"))
    return engine


def test_get_metadata_maps_joins(tmp_path):
    repo = SupabaseFilmRepository(engine=_seeded_engine(tmp_path))
    md = repo.get_metadata(41)
    assert md is not None
    assert md.title == "Hereditary"
    assert md.release_year == 2018  # derive de release_date
    assert md.genres == ["Drama", "Horror"]  # jointure, trie par nom
    assert md.rating == 7.3  # imdb prioritaire sur Rotten Tomatoes (echelle 0-100)
    assert md.synopsis.startswith("Une famille")


def test_get_metadata_absent(tmp_path):
    repo = SupabaseFilmRepository(engine=_seeded_engine(tmp_path))
    assert repo.get_metadata(999) is None

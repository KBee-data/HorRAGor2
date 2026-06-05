"""Test du chargeur de titres sur un mini SQLite temporaire (pas de dependance externe)."""

import sqlite3

import pytest

from backend.data.titles import load_titles


def _make_db(path) -> None:
    con = sqlite3.connect(path)
    con.execute("CREATE TABLE movies (id INTEGER PRIMARY KEY, title TEXT)")
    con.executemany(
        "INSERT INTO movies (id, title) VALUES (?, ?)",
        [(1, "The Thing"), (2, "Hereditary"), (3, None), (4, "")],
    )
    con.commit()
    con.close()


def test_load_titles_reads_pairs(tmp_path):
    db = tmp_path / "mini.db"
    _make_db(db)
    rows = load_titles(str(db))
    # Les titres NULL/vides sont exclus.
    assert rows == [(1, "The Thing"), (2, "Hereditary")]


def test_load_titles_missing_file_raises(tmp_path):
    with pytest.raises(FileNotFoundError):
        load_titles(str(tmp_path / "absent.db"))

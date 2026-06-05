"""Donnees bidon pour developper sans vraie base.

POURQUOI en dur ici : des donnees stables et previsibles rendent les tests
reproductibles. A remplacer par le golden data une fois fourni.
"""

from backend.contracts.schemas import FilmMetadata

FILMS: list[FilmMetadata] = [
    FilmMetadata(
        id=1,
        title="The Thing",
        director="John Carpenter",
        release_year=1982,
        genres=["Horreur"],
        rating=8.2,
        cast=["Kurt Russell", "Wilford Brimley"],
        synopsis="Une equipe en Antarctique affronte une creature qui imite ses victimes.",
    ),
    FilmMetadata(
        id=2,
        title="Hereditary",
        director="Ari Aster",
        release_year=2018,
        genres=["Horreur"],
        rating=7.3,
        cast=["Toni Collette", "Alex Wolff"],
        synopsis="Une famille est hantee par un heritage funeste apres un deuil.",
    ),
]

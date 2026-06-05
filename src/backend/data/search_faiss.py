"""Outil de calibration : interroge l'index FAISS et affiche les top-k avec leur score.

Sert a tester la qualite du matching et a regler le seuil (settings.faiss_score_threshold).

Lancement :
    uv run horragor-search "the thing"
    uv run horragor-search -k 10 "strangers chapter 3"
"""

import argparse

from backend.config import settings
from backend.data.embed import embed_text
from backend.data.faiss_index import TitleIndex, normalize_title


def main() -> None:
    parser = argparse.ArgumentParser(description="Recherche un titre dans l'index FAISS.")
    parser.add_argument("query", nargs="+", help="titre a rechercher")
    parser.add_argument("-k", type=int, default=5, help="nombre de resultats (defaut 5)")
    args = parser.parse_args()
    query = " ".join(args.query)

    index = TitleIndex.load()
    vector = embed_text(normalize_title(query))
    results = index.search_vector(vector, k=args.k)

    seuil = settings.faiss_score_threshold
    print(f"Requete : {query!r}  (seuil = {seuil}, {len(index)} titres indexes)")
    for score, film_id, title in results:
        flag = "OK " if score >= seuil else "  ."  # OK = au-dessus du seuil
        print(f"  {flag} {score:.3f}  id={film_id:<6} {title}")


if __name__ == "__main__":
    main()

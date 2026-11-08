"""Add one brand-new film to the catalog during the demo, to prove Copilot reads Atlas live.

    python demos/leafy-cinema/scripts/live_insert.py          # add "The Projectionist of Marigold Falls"
    python demos/leafy-cinema/scripts/live_insert.py --undo   # remove it again after the demo

The federated connector queries Atlas when the question is asked. There is no copy, no
sync job and no re-index. So a film added 30 seconds ago shows up in Copilot's next answer.
The film is fictional, and it is a perfect "hidden gem": 98% from 62 critics, 3,100 votes,
92 minutes, rated PG. It goes into both `movies` and `embedded_movies`, so find, aggregate
and vector search all see it. Running it twice is safe: the second run replaces the first.
"""

from __future__ import annotations

import sys as _sys
from pathlib import Path as _Path
_sys.path.insert(0, str(_Path(__file__).resolve().parents[3] / "common"))
import _env  # noqa: F401  loads the top-level .env

import argparse
import datetime as dt
import os
import sys
import time

from bson import ObjectId
from pymongo import MongoClient
from pymongo.errors import OperationFailure

FILM_ID = ObjectId("6a0000000000000000000001")
TITLE = "The Projectionist of Marigold Falls"
STORY = ("After sixty-one years in the projection booth of the Marigold Falls Theater, Earl Dunmore "
         "is told the cinema must switch to digital or close for good. Over one last summer, Earl, "
         "his granddaughter and a town that stopped going to the movies race to restore the old "
         "projector and fill every seat for one final screening on real film.")


def build(now: dt.datetime) -> dict:
    return {
        "_id": FILM_ID, "title": TITLE, "year": 2015, "type": "movie",
        "plot": "The last projectionist of a small-town cinema fights to save it for one more summer.",
        "fullplot": STORY, "genres": ["Documentary", "Drama"], "runtime": 92, "rated": "PG",
        "cast": ["Earl Dunmore", "June Dunmore"], "directors": ["Marian Voss"], "writers": ["Marian Voss"],
        "languages": ["English"], "countries": ["USA"],
        "released": dt.datetime(2015, 9, 4), "num_mflix_comments": 0,
        "awards": {"wins": 6, "nominations": 9, "text": "6 wins & 9 nominations."},
        "imdb": {"rating": 8.4, "votes": 3100, "id": 9999001},
        "tomatoes": {
            "viewer": {"rating": 4.4, "numReviews": 5200, "meter": 96},
            "critic": {"rating": 8.7, "numReviews": 62, "meter": 98},
            "fresh": 61, "rotten": 1, "production": "Marigold Pictures",
            "lastUpdated": now.strftime("%Y-%m-%d %H:%M:%S")},
        "lastupdated": now.strftime("%Y-%m-%d %H:%M:%S.000000000"),
    }


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--undo", action="store_true", help="remove the added film")
    ap.add_argument("--no-wait", action="store_true", help="skip waiting for the vector index")
    args = ap.parse_args()
    uri = os.environ.get("MONGODB_URI") or sys.exit("Set MONGODB_URI first.")
    db = MongoClient(uri)[os.environ.get("MONGODB_DB_MOVIES", "sample_mflix")]

    if args.undo:
        a = db.movies.delete_one({"_id": FILM_ID}).deleted_count
        b = db.embedded_movies.delete_one({"_id": FILM_ID}).deleted_count
        print(f"removed {a} film from movies and {b} from embedded_movies. Catalog is back to the original data.")
        return

    film = build(dt.datetime.now().replace(microsecond=0))
    db.movies.replace_one({"_id": FILM_ID}, film, upsert=True)
    db.embedded_movies.replace_one({"_id": FILM_ID}, film, upsert=True)
    print(f"added {TITLE} (2015): 98% from 62 critics, 3,100 IMDb votes, 92 min, PG, "
          f"lastupdated {film['lastupdated'][:19]}")
    if args.no_wait:
        return
    # Automated Embedding runs asynchronously. Wait until vector search can see the film.
    pipeline = [
        {"$vectorSearch": {"index": "vector_index_fullplot", "path": "fullplot",
                           "query": {"text": STORY}, "numCandidates": 100, "limit": 3}},
        {"$project": {"_id": 1}},
    ]
    start = time.time()
    while time.time() - start < 60:
        try:
            if any(r["_id"] == FILM_ID for r in db.embedded_movies.aggregate(pipeline)):
                print(f"vector search sees it after {time.time() - start:.0f}s")
                return
        except OperationFailure as e:
            # Show the server's message only. It never contains the connection string.
            reason = (e.details or {}).get("errmsg") or str(e)
            print(f"vector search failed: {reason}\n"
                  "Find and aggregate already see the film. Check the index vector_index_fullplot (see README.md).")
            return
        time.sleep(2)
    print("vector search does not see it yet after 60s; find and aggregate already do")


if __name__ == "__main__":
    main()

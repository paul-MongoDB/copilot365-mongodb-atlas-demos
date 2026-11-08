"""Run the movie demo's queries straight against Atlas and print what Copilot should find.

    python demos/leafy-cinema/scripts/demo_queries.py            # all queries
    python demos/leafy-cinema/scripts/demo_queries.py --check    # exit 1 if a number drifted

Read-only. Use it to confirm the data and the vector index before the demo.
"""

from __future__ import annotations

import sys as _sys
from pathlib import Path as _Path
_sys.path.insert(0, str(_Path(__file__).resolve().parents[3] / "common"))
import _env  # noqa: F401  loads the top-level .env

import argparse
import os
import sys

from pymongo import MongoClient

DB = os.environ.get("MONGODB_DB_MOVIES", "sample_mflix")

# The customer's half-remembered description, exactly as Dana posts it in Teams.
CUSTOMER_STORY = ("angels who watch over a city and can hear what everyone is thinking, "
                  "and one of them wants to become human because he falls in love with a trapeze artist")

DRAFT = [  # Helen's draft lineup (title, year)
    ("Song of the Sea", 2014), ("'71", 2014), ("Murderball", 2005),
    ("Leviathan", 2014), ("The Fog of War: Eleven Lessons from the Life of Robert S. McNamara", 2003),
    ("Wings of Desire", 1987)]


def fee(year: int) -> int:
    """License rate card: by release year."""
    return 500 if year < 1970 else 650 if year < 1990 else 750 if year < 2000 else 850 if year < 2010 else 1000


LAST_YEAR = {"Spellbound", "The Man Without a Past", "The Fog of War: Eleven Lessons from the Life of Robert S. McNamara",
             "Wadjda", "Winged Migration", "Monsieur Lazhar"}
REFERENCE_FIX = [("Song of the Sea", 2014), ("'71", 2014), ("Murderball", 2005),
                 ("The Adventures of Robin Hood", 1938), ("The Rules of the Game", 1939), ("Belle de Jour", 1967)]


def problems(films: list[dict], budget: int = 4800) -> list[str]:
    """Check a six-film lineup against every rule in the guidelines, the rate card and Teams."""
    out = []
    for d in films:
        c = d["tomatoes"]["critic"]
        if not (c.get("meter", 0) >= 95 and c.get("numReviews", 0) >= 40 and d["imdb"]["votes"] < 50_000):
            out.append(f"{d['title']}: not a hidden gem")
        if d["runtime"] > 125:
            out.append(f"{d['title']}: {d['runtime']} min is over the 125-minute limit")
        if d["title"] in LAST_YEAR:
            out.append(f"{d['title']}: played last year")
    if sum(d["rated"] == "R" for d in films) > 2:
        out.append("more than 2 R-rated films")
    if sum(d["languages"][0] != "English" for d in films) < 2:
        out.append("fewer than 2 non-English films")
    dirs = [x for d in films for x in d["directors"]]
    if len(dirs) != len(set(dirs)):
        out.append("a director appears twice")
    total = sum(fee(d["year"]) for d in films)
    if total > budget:
        out.append(f"total ${total:,} is over the ${budget:,} budget by ${total - budget:,}")
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()
    uri = os.environ.get("MONGODB_URI") or sys.exit("Set MONGODB_URI (or put it in .env).")
    db = MongoClient(uri, serverSelectionTimeoutMS=10_000)[DB]
    movies, emb = db.movies, db.embedded_movies
    bad = []

    print("== Setup")
    idx = {i["name"]: i.get("queryable") for i in emb.list_search_indexes()}
    print("   movies:", movies.estimated_document_count(), " embedded_movies:", emb.estimated_document_count(),
          " vector index vector_index_fullplot queryable:", idx.get("vector_index_fullplot"))
    if not idx.get("vector_index_fullplot"):
        bad.append("vector_index_fullplot is missing or not ready")

    print("\n== Prompt 4: the customer's half-remembered movie (vector search on fullplot)")
    top = list(emb.aggregate([
        {"$vectorSearch": {"index": "vector_index_fullplot", "path": "fullplot",
                           "query": {"text": CUSTOMER_STORY}, "numCandidates": 200, "limit": 3}},
        {"$project": {"title": 1, "year": 1, "score": {"$meta": "vectorSearchScore"}}}]))
    for d in top:
        print(f"   {d['title']} ({d['year']})  score {d['score']:.3f}")
    if not top or top[0]["title"] != "Wings of Desire":
        bad.append("Prompt 4 top match is not Wings of Desire")

    print("\n== Prompt 2: hidden gems (critics 95%+, 40+ critic reviews, under 15,000 IMDb votes)")
    gems = list(movies.aggregate([
        {"$match": {"type": "movie", "tomatoes.critic.meter": {"$gte": 95},
                    "tomatoes.critic.numReviews": {"$gte": 40}, "imdb.votes": {"$lt": 15_000}}},
        {"$sort": {"tomatoes.critic.numReviews": -1, "imdb.votes": 1}},
        {"$facet": {"top": [{"$limit": 10}], "n": [{"$count": "n"}]}}]))[0]
    print("   qualifying films:", gems["n"][0]["n"])
    for d in gems["top"]:
        t = d["tomatoes"]["critic"]
        print(f"   {d['title'][:42]:42} {d['year']}  {d.get('runtime')}m  {d.get('rated')}  "
              f"critics {t['meter']}% of {t['numReviews']}  votes {d['imdb']['votes']:,}")

    print("\n== Prompt 3: critics loved it, audiences did not (40+ critic reviews, 10,000+ audience ratings)")
    gap = list(movies.aggregate([
        {"$match": {"type": "movie", "tomatoes.critic.numReviews": {"$gte": 40},
                    "tomatoes.viewer.numReviews": {"$gte": 10_000},
                    "tomatoes.critic.meter": {"$exists": True}, "tomatoes.viewer.meter": {"$exists": True}}},
        {"$project": {"title": 1, "year": 1, "critic": "$tomatoes.critic.meter", "audience": "$tomatoes.viewer.meter",
                      "gap": {"$subtract": ["$tomatoes.critic.meter", "$tomatoes.viewer.meter"]}}},
        {"$sort": {"gap": -1}}, {"$limit": 5}]))
    for d in gap:
        print(f"   {d['title']} ({d['year']})  critics {d['critic']}%  audiences {d['audience']}%  gap {d['gap']}")
    if not gap or gap[0]["title"] != "Spy Kids":
        bad.append("Prompt 3 top gap is not Spy Kids")

    print("\n== Prompt 1: anything added today? (lastupdated starts with today's year-month-day)")
    import datetime as dt
    today = dt.date.today().isoformat()
    n = movies.count_documents({"lastupdated": {"$regex": f"^{today}"}})
    print(f"   {n} films added on {today}   (expect 0 before the live insert, 1 after)")

    print("\n== Prompt 5: Helen's draft lineup")
    total = 0
    rows = []
    for title, year in DRAFT:
        d = movies.find_one({"title": title, "year": year, "type": "movie"})
        if not d:
            bad.append(f"missing film {title} {year}")
            continue
        f = fee(d["year"])
        total += f
        rows.append(d)
        print(f"   {d['title'][:30]:30} {d['year']}  {d['runtime']:>3}m  {d['rated']:6} ${f:,}  {d['languages'][0]}")
    r_count = sum(d["rated"] == "R" for d in rows)
    print(f"   total ${total:,} against $4,800 budget (over by ${total - 4800:,}); R-rated: {r_count} (max 2); "
          f"over 125 min: {[d['title'] for d in rows if d['runtime'] > 125]}")
    if (total, r_count) != (5350, 3):
        bad.append("Prompt 5 totals changed")

    print("   problems in the draft:", *problems(rows), sep="\n     - ")
    ref = [movies.find_one({"title": t, "year": y, "type": "movie"}) for t, y in REFERENCE_FIX]
    ref_problems = problems(ref)
    print("   one valid fix (swap the last three):", [(d["title"], d["year"], f"${fee(d['year']):,}") for d in ref[3:]],
          "total", f"${sum(fee(d['year']) for d in ref):,}", "problems:", ref_problems or "none")
    if ref_problems:
        bad.append("reference fix is not valid")

    print("\n== Q&A")
    print("   theaters by state:", [(r["_id"], r["n"]) for r in db.theaters.aggregate(
        [{"$group": {"_id": "$location.address.state", "n": {"$sum": 1}}}, {"$sort": {"n": -1}}, {"$limit": 5}])])
    print("   closest theaters to downtown Minneapolis:", [
        (r["location"]["address"]["city"], round(r["dist"] / 1609.34, 1)) for r in db.theaters.aggregate(
            [{"$geoNear": {"near": {"type": "Point", "coordinates": [-93.265, 44.978]},
                           "distanceField": "dist", "spherical": True}}, {"$limit": 3}])])
    print("   directors, 6+ films since 1980, best average IMDb rating:", [
        (r["_id"], r["n"], round(r["avg"], 2)) for r in movies.aggregate([
            {"$match": {"type": "movie", "year": {"$type": "int", "$gte": 1980}, "imdb.rating": {"$type": "number"}}},
            {"$unwind": "$directors"},
            {"$group": {"_id": "$directors", "n": {"$sum": 1}, "avg": {"$avg": "$imdb.rating"}}},
            {"$match": {"n": {"$gte": 6}}}, {"$sort": {"avg": -1}}, {"$limit": 3}])])

    if bad:
        print("\nPROBLEMS:", *bad, sep="\n  - ")
    return 1 if (bad and args.check) else 0


if __name__ == "__main__":
    sys.exit(main())

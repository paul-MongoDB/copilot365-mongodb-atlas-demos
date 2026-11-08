"""Run the queries behind the demo prompts and the Q&A prompts, plus a few extra
queries, and print the answers. It only reads; it never changes data.

Use it the day before the demo to see what Copilot should say. From the repo root,
with MONGODB_URI set in the root .env file:

    .venv/bin/python demos/insurance-claims/scripts/demo_queries.py            # find and aggregate queries
    .venv/bin/python demos/insurance-claims/scripts/demo_queries.py --vector   # also run $vectorSearch (Atlas only)

Which output answers which prompt:
    F1  Prompt 1 (the claim record)
    A2  Prompt 2 (contractor comparison)
    V1  Prompt 3 (vector search; needs --vector)
    K1  the keyword contrast you quote after Prompt 3
    A1, A5, A6  the Q&A prompts (hailstorm, Shady Elm sewer backups, denied sewer backups)
    F2, F3, A3, A4  extra queries for questions from the audience
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "common"))
import _env  # noqa: F401  loads the top-level .env

from pymongo import MongoClient

OPEN = ["Open", "Under Review", "Pending Documents"]

FIND = {
    "F1  Show me claim CLM-2026-10482": (
        "claims", {"_id": "CLM-2026-10482"},
        {"_id": 1, "insured_name": 1, "status": 1, "claimed_amount": 1, "reserve_amount": 1,
         "contractor": 1, "pricing_guide_estimate": 1, "assigned_adjuster": 1, "policy_number": 1},
        None,
    ),
    "F2  Open claims assigned to Maya Chen with more than $25,000 claimed": (
        "claims",
        {"assigned_adjuster": "Maya Chen", "status": {"$in": OPEN}, "claimed_amount": {"$gt": 25_000}},
        {"_id": 1, "insured_name": 1, "peril": 1, "status": 1, "claimed_amount": 1},
        [("claimed_amount", -1)],
    ),
    "F3  Coverage and endorsements on policy POL-HO-778301": (
        "policies", {"_id": "POL-HO-778301"},
        {"named_insured": 1, "coverage": 1, "deductibles": 1, "endorsements.code": 1, "inception_date": 1},
        None,
    ),
}

AGG = {
    "A1  Hailstorm CAT-2026-17: claims, reserves and paid by city": ("claims", [
        {"$match": {"cat_event.code": "CAT-2026-17"}},
        {"$group": {"_id": "$property_address.city", "claims": {"$sum": 1},
                    "open_reserves": {"$sum": "$reserve_amount"}, "paid": {"$sum": "$paid_amount"}}},
        {"$sort": {"claims": -1}},
    ]),
    "A2  Water claims since Aug 1 by contractor: count, avg estimate, % over pricing guide": ("claims", [
        {"$match": {"peril": {"$regex": "^Water"}, "date_of_loss": {"$gte": dt.datetime(2026, 8, 1)},
                    "contractor": {"$ne": None}}},
        {"$group": {"_id": "$contractor.name", "claims": {"$sum": 1},
                    "avg_estimate": {"$avg": "$contractor.estimate_amount"},
                    "avg_pct_over_guide": {"$avg": {"$multiply": [100, {"$subtract": [
                        {"$divide": ["$contractor.estimate_amount", "$pricing_guide_estimate"]}, 1]}]}},
                    "already_paid": {"$sum": "$paid_amount"},
                    "aob_signed": {"$sum": {"$cond": ["$assignment_of_benefits", 1, 0]}}}},
        {"$project": {"claims": 1, "already_paid": 1, "aob_signed": 1,
                      "avg_estimate": {"$round": ["$avg_estimate", 0]},
                      "avg_pct_over_guide": {"$round": ["$avg_pct_over_guide", 1]}}},
        {"$sort": {"avg_pct_over_guide": -1}},
    ]),
    "A3  Open claims and reserves by adjuster": ("claims", [
        {"$match": {"status": {"$in": OPEN}}},
        {"$group": {"_id": "$assigned_adjuster", "open_claims": {"$sum": 1},
                    "total_reserves": {"$sum": "$reserve_amount"}}},
        {"$sort": {"open_claims": -1}},
    ]),
    "A4  Average days to report and to close, by peril (closed claims)": ("claims", [
        {"$match": {"date_closed": {"$ne": None}}},
        {"$group": {"_id": "$peril", "closed": {"$sum": 1},
                    "avg_days_to_report": {"$avg": {"$dateDiff": {
                        "startDate": "$date_of_loss", "endDate": "$date_reported", "unit": "day"}}},
                    "avg_days_to_close": {"$avg": {"$dateDiff": {
                        "startDate": "$date_reported", "endDate": "$date_closed", "unit": "day"}}}}},
        {"$project": {"closed": 1, "avg_days_to_report": {"$round": ["$avg_days_to_report", 1]},
                      "avg_days_to_close": {"$round": ["$avg_days_to_close", 1]}}},
        {"$sort": {"avg_days_to_close": -1}},
    ]),
    "A5  Open sewer-backup claims and whether the policy has water backup coverage ($lookup)": ("claims", [
        {"$match": {"peril": "Water - Sewer Backup", "status": {"$in": OPEN}}},
        {"$lookup": {"from": "policies", "localField": "policy_number", "foreignField": "_id", "as": "policy"}},
        {"$unwind": "$policy"},
        {"$project": {"insured_name": 1, "claimed_amount": 1, "street": "$property_address.street",
                      "endorsements": "$policy.endorsements.code",
                      "has_water_backup": {"$gt": [{"$size": {"$filter": {
                          "input": "$policy.endorsements.code", "as": "c",
                          "cond": {"$eq": [{"$substrCP": ["$$c", 0, 5]}, "HO-WB"]}}}}, 0]}}},
    ]),
    "A6  Sewer backups denied for lacking the endorsement (upsell signal)": ("claims", [
        {"$match": {"denial_reason": {"$regex": "no HO-WB"}}},
        {"$group": {"_id": None, "denied_claims": {"$sum": 1}, "total_claimed": {"$sum": "$claimed_amount"}}},
    ]),
}

VECTOR_QUERY = ("homeowner was away from home, came back to water coming through a ceiling under "
                "an upstairs bathroom, and a restoration company showed up right away and "
                "recommended tearing everything out")


def show(rows) -> None:
    for r in rows:
        print("   ", json.dumps(r, default=str))


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--vector", action="store_true", help="also run the $vectorSearch query (Atlas only)")
    args = ap.parse_args()
    uri = os.environ.get("MONGODB_URI")
    if not uri:
        sys.exit("Set MONGODB_URI first.")
    db = MongoClient(uri)[os.environ.get("MONGODB_DB", "contoso_claims")]

    for title, (coll, flt, proj, sort) in FIND.items():
        print(f"\n{title}\n    db.{coll}.find({json.dumps(flt)})")
        cur = db[coll].find(flt, proj)
        if sort:
            cur = cur.sort(sort)
        show(cur)

    for title, (coll, pipeline) in AGG.items():
        print(f"\n{title}")
        show(db[coll].aggregate(pipeline))

    print("\nK1  Keyword contrast: claims whose description mentions 'ceiling'")
    hits = list(db.claims.find({"loss_description": {"$regex": "ceiling", "$options": "i"}},
                               {"peril": 1, "contractor.name": 1}))
    by_peril = ", ".join(f"{n} {p}" for p, n in Counter(r["peril"] for r in hits).most_common())
    print(f"    {len(hits)} hits: {by_peril}")
    for r in hits:
        print(f"    {r['_id']}  {r['peril']:<20} {(r.get('contractor') or {}).get('name')}")

    if args.vector:
        print(f"\nV1  $vectorSearch: \"{VECTOR_QUERY}\"")
        pipeline = [
            {"$vectorSearch": {"index": "claims_semantic", "path": "loss_description",
                               "query": VECTOR_QUERY, "numCandidates": 150, "limit": 10}},
            {"$project": {"insured_name": 1, "peril": 1, "contractor": "$contractor.name",
                          "city": "$property_address.city",
                          "score": {"$meta": "vectorSearchScore"}}},
        ]
        for r in db.claims.aggregate(pipeline):
            print(f"    {r['score']:.3f}  {r['_id']}  {r['city']:<9} {r.get('contractor')}")


if __name__ == "__main__":
    main()

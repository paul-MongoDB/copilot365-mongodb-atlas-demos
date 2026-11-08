"""Run the Atlas side of every demo prompt, and print the expected answers. Read-only.

    python demos/leafy-tech/scripts/demo_queries.py           # print the answers
    python demos/leafy-tech/scripts/demo_queries.py --check   # also exit 1 if a number drifted
    python demos/leafy-tech/scripts/demo_queries.py --hood    # the "under the hood" view for the audience
    python demos/leafy-tech/scripts/demo_queries.py --pipeline  # the warranty aggregation, for the audience
"""

from __future__ import annotations

import sys as _sys
from pathlib import Path as _Path
_sys.path.insert(0, str(_Path(__file__).resolve().parents[3] / "common"))
import _env  # noqa: F401  loads the top-level .env

import argparse
import datetime as dt
import json
import os
import sys

from pymongo import MongoClient

CUSTOMER_WORDS = ("Our nurses push a cart from room to room all shift. It gets wiped down with harsh cleaning "
                  "chemicals between every patient, it cannot die halfway through a 12-hour shift, and it gets "
                  "knocked off the cart a few times a year.")
CUTOFF = dt.datetime(2027, 2, 1)   # warranties ending on or before January 31, 2027
QUOTE = "Q-2026-4471"
FIXED_LINES = [("FB-MB14C", 10), ("WT-CD2", 10), ("FB-W4", 10), ("LT-IMG", 0)]  # (sku, discount %)
QTY = 500
REBATE_PCT = 4

failures: list[str] = []


def check(label: str, got, want) -> None:
    ok = got == want
    print(f"  {'ok ' if ok else 'BAD'} {label}: {got}" + ("" if ok else f" (expected {want})"))
    if not ok:
        failures.append(label)


def vector_match(db, limit: int = 5) -> list[dict]:
    return list(db.products.aggregate([
        {"$vectorSearch": {"index": "product_semantic", "path": "description", "query": {"text": CUSTOMER_WORDS},
                           "numCandidates": 200, "limit": limit}},
        {"$project": {"_id": 0, "name": 1, "score": {"$meta": "vectorSearchScore"}}}]))


WARRANTY_PIPELINE = [
    {"$unwind": "$devices"},
    {"$match": {"devices.warranty_end": {"$gte": dt.datetime(2026, 11, 1), "$lt": CUTOFF}}},
    {"$group": {"_id": "$name", "industry": {"$first": "$industry"}, "am": {"$first": "$account_manager"},
                "devices": {"$sum": "$devices.qty"}, "spend": {"$first": "$spend_last_12_months"}}},
    {"$sort": {"devices": -1, "_id": 1}},
    {"$limit": 11},
]


def warranties(db) -> list[dict]:
    return list(db.customers.aggregate(WARRANTY_PIPELINE))


def show_pipeline(db) -> None:
    print("The pipeline, one stage per step:\n")
    print(json.dumps(WARRANTY_PIPELINE[:-1] + [{"$limit": 10}], indent=2, default=lambda d: d.strftime("%Y-%m-%d")))
    print("\nThe result:\n")
    for r in warranties(db)[:10]:
        print(f"  {r['devices']:>4} devices  {r['_id']} ({r['am']})")


def cross_sell(db) -> list[dict]:
    return list(db.customers.find({"industry": "Healthcare", "spend_by_category.Security": 0},
                                  {"_id": 0, "name": 1, "account_manager": 1, "spend_last_12_months": 1})
                .sort("spend_last_12_months", -1).limit(5))


def quote_math(db) -> dict:
    prices = {p["sku"]: p for p in db.products.find({}, {"sku": 1, "list_price": 1, "cost": 1})}
    q = db.quotes.find_one({"quote_number": QUOTE})
    cost = sum(prices[x["sku"]]["cost"] * x["qty"] for x in q["lines"])
    fixed_total = sum(prices[s]["list_price"] * (100 - d) / 100 * QTY for s, d in FIXED_LINES)
    fixed_cost = sum(prices[s]["cost"] * QTY for s, _ in FIXED_LINES)
    return {"draft_total": q["total"], "draft_margin": round((q["total"] - cost) / q["total"] * 100, 1),
            "fixed_total": fixed_total, "fixed_margin": round((fixed_total - fixed_cost) / fixed_total * 100, 1),
            "rebate": prices["FB-MB14C"]["cost"] * QTY * REBATE_PCT / 100}


def hood(db) -> None:
    idx = next(iter(db.products.list_search_indexes("product_semantic")))
    print("1. The whole vector index. Atlas embeds `description` itself with voyage-4:\n")
    print(json.dumps(idx["latestDefinition"], indent=2))
    doc = db.products.find_one({"sku": "FB-MB14C"}, {"_id": 0, "sku": 1, "name": 1, "list_price": 1, "stock": 1})
    print("\n2. The product document. No vector field in it, and stock lives inside the product:\n")
    print(json.dumps(doc, indent=2))
    print("\n3. The query. Plain English goes straight into $vectorSearch:\n")
    print(json.dumps({"$vectorSearch": {"index": "product_semantic", "path": "description",
                                        "query": {"text": CUSTOMER_WORDS[:60] + "..."},
                                        "numCandidates": 200, "limit": 3}}, indent=2))
    print()
    for r in vector_match(db, 3):
        print(f"  {r['score']:.3f}  {r['name']}")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--hood", action="store_true")
    ap.add_argument("--pipeline", action="store_true")
    args = ap.parse_args()
    uri = os.environ.get("MONGODB_URI") or sys.exit("Set MONGODB_URI first.")
    db = MongoClient(uri)[os.environ.get("MONGODB_DB_TECH", "leafy_tech")]
    if args.hood:
        hood(db)
        return
    if args.pipeline:
        show_pipeline(db)
        return

    print("Prompt 4: meaning search")
    matches = vector_match(db)
    for r in matches:
        print(f"  {r['score']:.3f}  {r['name']}")
    check("top match", matches[0]["name"], "Fabrikam MedBook 14 Clinical")

    print("Prompt 3: warranties ending by Jan 31, 2027")
    rows = warranties(db)
    for r in rows:
        print(f"  {r['_id']} | {r['industry']} | {r['am']} | {r['devices']} devices | ${r['spend']:,}")
    check("first customer", rows[0]["_id"], "Willow Bend Health")
    check("no tie at rank 10", rows[9]["devices"] != rows[10]["devices"], True)

    print("Prompt 2: healthcare customers with no security spend")
    for r in cross_sell(db):
        print(f"  {r['name']} | {r['account_manager']} | ${r['spend_last_12_months']:,}")

    print("Prompt 1: stock")
    stock = db.products.find_one({"sku": "FB-MB14C"})["stock"]
    for s in stock:
        print(f"  {s['warehouse']}: on hand {s['on_hand']}, reserved {s['reserved']}, available {s['available']}")
    check("available before the truck", sum(s["available"] for s in stock), 320)
    check("G2 docks available", sum(s["available"] for s in db.products.find_one({"sku": "WT-CD2"})["stock"]) >= QTY, True)

    print("Prompt 5: the quote")
    m = quote_math(db)
    check("draft total", m["draft_total"], 930950.0)
    check("draft margin", m["draft_margin"], 14.1)
    check("corrected total", m["fixed_total"], 1003500.0)
    check("corrected margin", m["fixed_margin"], 18.3)
    check("rebate", m["rebate"], 27000.0)
    check("deal registration on the quote", db.quotes.find_one({"quote_number": QUOTE})["deal_registration_id"], None)

    if args.check and failures:
        sys.exit(f"\nDRIFT: {', '.join(failures)}")
    print("\nall checks passed" if not failures else f"\n{len(failures)} check(s) differ")


if __name__ == "__main__":
    main()

"""Insert one new LeafyDry claim during the demo, to prove Copilot reads Atlas live.

    python scripts/live_insert.py          # insert CLM-2026-10531 (reported "now")
    python scripts/live_insert.py --undo   # remove it again after the demo

The federated connector queries Atlas when the question is asked. There is no
copy, no sync job and no re-index. So a claim inserted 30 seconds ago shows up
in Copilot's next answer. With Automated Embedding, Atlas also embeds the new
description by itself, so vector search finds it too.

Running it twice is safe: the second run replaces the first insert.
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

from pymongo import MongoClient
from pymongo.errors import OperationFailure

CLAIM_ID = "CLM-2026-10531"
POLICY_ID = "POL-HO-790415"


def build(now: dt.datetime) -> tuple[dict, dict]:
    loss = (now - dt.timedelta(days=1)).replace(hour=20, minute=40, second=0, microsecond=0)
    addr = {"street": "1907 Copper Canyon Rd", "city": "McKinney", "county": "Collin",
            "state": "TX", "zip": "75071"}
    policy = {
        "_id": POLICY_ID, "policy_number": POLICY_ID, "form": "HO-3",
        "named_insured": "Ryan and Katie Holloway", "property_address": addr,
        "inception_date": dt.datetime(2021, 3, 1), "effective_date": dt.datetime(2026, 3, 1),
        "expiration_date": dt.datetime(2027, 3, 1),
        "coverage": {"A_dwelling": 455_000, "B_other_structures": 45_500,
                     "C_personal_property": 227_500, "D_loss_of_use": 91_000,
                     "E_personal_liability": 300_000, "F_medical_payments": 5_000},
        "deductibles": {"all_peril": 2_500, "wind_hail_pct": 0.01},
        "endorsements": [], "annual_premium": 4_650, "agent": "Contoso Direct",
    }
    claim = {
        "_id": CLAIM_ID, "claim_number": CLAIM_ID, "policy_number": POLICY_ID,
        "insured_name": "Ryan and Katie Holloway", "property_address": addr,
        "line_of_business": "Homeowners", "peril": "Water - Plumbing", "cat_event": None,
        "date_of_loss": loss, "date_reported": now, "date_closed": None,
        "status": "Open", "assigned_adjuster": "Maya Chen",
        "claimed_amount": 42_600, "reserve_amount": 36_000, "paid_amount": 0,
        "deductible_applied": 2_500,
        "contractor": {"name": "LeafyDry Restoration LLC", "estimate_amount": 42_600},
        "pricing_guide_estimate": 30_900, "assignment_of_benefits": True, "denial_reason": None,
        "loss_description": (
            "We got home last night from our son's soccer tournament in Houston and water was "
            "dripping through the ceiling fan in the game room, right under the kids' bathroom. "
            "A crew from LeafyDry pulled up within the hour and said the ceiling, the walls and "
            "the bathroom floor all have to be replaced."),
        "adjuster_notes": [{"date": now, "author": "Maya Chen",
                            "note": "New claim. Assignment of benefits to LeafyDry Restoration LLC "
                                    "received, signed on the date of loss."}],
    }
    return claim, policy


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--undo", action="store_true", help="remove the inserted claim and policy")
    ap.add_argument("--no-wait", action="store_true", help="skip waiting for the vector index")
    args = ap.parse_args()
    uri = os.environ.get("MONGODB_URI") or sys.exit("Set MONGODB_URI first.")
    db = MongoClient(uri)[os.environ.get("MONGODB_DB", "contoso_claims")]

    if args.undo:
        c = db.claims.delete_one({"_id": CLAIM_ID}).deleted_count
        p = db.policies.delete_one({"_id": POLICY_ID}).deleted_count
        print(f"removed {c} claim and {p} policy. Data is back to the scripted state.")
        return

    claim, policy = build(dt.datetime.now().replace(microsecond=0))
    db.policies.replace_one({"_id": POLICY_ID}, policy, upsert=True)
    db.claims.replace_one({"_id": CLAIM_ID}, claim, upsert=True)
    print(f"inserted {CLAIM_ID}: Holloway, McKinney, LeafyDry estimate $42,600, "
          f"reported {claim['date_reported']:%H:%M}")

    if args.no_wait:
        return
    # Automated Embedding runs asynchronously. Wait until vector search can see the claim.
    pipeline = [
        {"$vectorSearch": {"index": "claims_semantic", "path": "loss_description",
                           "query": claim["loss_description"], "numCandidates": 50, "limit": 3}},
        {"$project": {"_id": 1}},
    ]
    start = time.time()
    while time.time() - start < 60:
        try:
            if any(r["_id"] == CLAIM_ID for r in db.claims.aggregate(pipeline)):
                print(f"vector search sees it after {time.time() - start:.0f}s")
                return
        except OperationFailure:
            print("no vector index on this deployment; find and aggregate already see the claim")
            return
        time.sleep(2)
    print("vector search does not see it yet after 60s; find and aggregate already do")


if __name__ == "__main__":
    main()

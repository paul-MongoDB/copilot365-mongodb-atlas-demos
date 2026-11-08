"""Land a truck at the Chicago warehouse during the demo, to prove Copilot reads Atlas live.

    python demos/leafy-tech/scripts/live_insert.py          # 180 MedBooks arrive: 320 -> 500 available
    python demos/leafy-tech/scripts/live_insert.py --undo   # back to 320, receipt removed

One receipt goes into `receipts` and the product's Chicago stock goes from 150 to 330. Both
values are set outright, so running it twice is safe.
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

from pymongo import MongoClient

SKU, NAME, WAREHOUSE = "FB-MB14C", "Fabrikam MedBook 14 Clinical", "Chicago"
BEFORE, ARRIVING = 150, 180
RECEIPT = "RCV-2026-11877"


def set_chicago(db, qty: int) -> None:
    db.products.update_one(
        {"sku": SKU, "stock.warehouse": WAREHOUSE},
        {"$set": {"stock.$.on_hand": qty, "stock.$.available": qty}})


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--undo", action="store_true", help="remove the receipt and restore the stock")
    args = ap.parse_args()
    uri = os.environ.get("MONGODB_URI") or sys.exit("Set MONGODB_URI first.")
    db = MongoClient(uri)[os.environ.get("MONGODB_DB_TECH", "leafy_tech")]

    if args.undo:
        set_chicago(db, BEFORE)
        n = db.receipts.delete_many({"receipt_number": RECEIPT}).deleted_count
        print(f"removed {n} receipt. Chicago is back to {BEFORE}.")
    else:
        set_chicago(db, BEFORE + ARRIVING)
        db.receipts.replace_one({"receipt_number": RECEIPT}, {
            "receipt_number": RECEIPT, "sku": SKU, "product": NAME, "warehouse": WAREHOUSE, "qty": ARRIVING,
            "received_at": dt.datetime.now(dt.timezone.utc).replace(microsecond=0)}, upsert=True)
        print(f"received {ARRIVING} x {NAME} at {WAREHOUSE}")

    stock = db.products.find_one({"sku": SKU})["stock"]
    print(" ".join(f"{s['warehouse']} {s['available']}" for s in stock), f"= {sum(s['available'] for s in stock)} available")


if __name__ == "__main__":
    main()

"""Load the Leafy Tech data into Atlas and create the indexes the demo needs.

    python demos/leafy-tech/scripts/load_atlas.py

Database: leafy_tech (override with MONGODB_DB_TECH). It touches only that database. It drops
and reloads customers, orders and quotes, and drops receipts (live_insert.py's truck). It empties
products and reloads it without dropping it, so the vector index on products survives. Atlas
Automated Embedding embeds products.description, so $vectorSearch takes plain English and no
vectors live in the documents.
"""

from __future__ import annotations

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "common"))
import _env  # noqa: F401  loads the top-level .env

import argparse
import os
import time

from bson import json_util
from pymongo import ASCENDING, DESCENDING, MongoClient
from pymongo.errors import OperationFailure
from pymongo.operations import SearchIndexModel

ROOT = Path(__file__).resolve().parent.parent
VECTOR_INDEX = "product_semantic"
VECTOR_DEFINITION = {
    "fields": [
        {"type": "autoEmbed", "modality": "text", "path": "description", "model": "voyage-4"},
        {"type": "filter", "path": "category"},
        {"type": "filter", "path": "status"},
    ]
}


def main() -> None:
    uri = os.environ.get("MONGODB_URI") or sys.exit("Set MONGODB_URI first.")
    db = MongoClient(uri)[os.environ.get("MONGODB_DB_TECH", "leafy_tech")]

    db.receipts.drop()
    for name in ("customers", "orders", "quotes"):
        docs = json_util.loads((ROOT / "data" / f"{name}.json").read_text())
        db[name].drop()
        db[name].insert_many(docs)
        print(f"{name}: {len(docs)}")
    # products keeps its vector index across reloads, so replace the documents, not the collection.
    docs = json_util.loads((ROOT / "data" / "products.json").read_text())
    db.products.delete_many({})
    db.products.insert_many(docs)
    print(f"products: {len(docs)}")

    db.products.create_index([("sku", ASCENDING)], unique=True)
    db.products.create_index([("category", ASCENDING), ("status", ASCENDING)])
    db.customers.create_index([("name", ASCENDING)])
    db.customers.create_index([("industry", ASCENDING), ("spend_last_12_months", DESCENDING)])
    db.customers.create_index([("devices.warranty_end", ASCENDING)])
    db.orders.create_index([("customer_id", ASCENDING), ("order_date", DESCENDING)])
    db.quotes.create_index([("quote_number", ASCENDING)], unique=True)
    print("b-tree indexes created")

    if not next(iter(db.products.list_search_indexes(VECTOR_INDEX)), None):
        try:
            db.products.create_search_index(
                SearchIndexModel(definition=VECTOR_DEFINITION, name=VECTOR_INDEX, type="vectorSearch"))
        except OperationFailure as e:
            sys.exit(f"Could not create the vector index: {e}")

    print(f"vector index '{VECTOR_INDEX}': waiting for it to build", end="", flush=True)
    for _ in range(120):
        idx = next(iter(db.products.list_search_indexes(VECTOR_INDEX)), None)
        if idx and idx.get("queryable"):
            print(" ready")
            return
        print(".", end="", flush=True)
        time.sleep(5)
    print("\nStill building after 10 minutes. Check the Atlas UI.")


if __name__ == "__main__":
    # No options: this only makes --help print the description instead of running.
    argparse.ArgumentParser(description=__doc__,
                            formatter_class=argparse.RawDescriptionHelpFormatter).parse_args()
    main()

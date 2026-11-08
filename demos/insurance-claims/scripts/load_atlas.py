"""Load the demo data into MongoDB and create the indexes the demo needs.

Usage:
    export MONGODB_URI="mongodb+srv://<user>:<password>@<cluster-host>/"
    python scripts/load_atlas.py            # drop + reload claims and policies
    python scripts/load_atlas.py --no-vector  # skip the vector index (local testing)

Database: contoso_claims (override with MONGODB_DB).

The vector index uses Atlas Automated Embedding (index type "autoEmbed"):
Atlas embeds claims.loss_description with Voyage AI at index time, and embeds
the query text at query time. No embedding code, no vectors in the documents,
and $vectorSearch takes plain English in its "query" field. That matters for
Copilot: the connector can pass the user's words straight through.
"""

from __future__ import annotations

import sys as _sys
from pathlib import Path as _Path
_sys.path.insert(0, str(_Path(__file__).resolve().parents[3] / "common"))
import _env  # noqa: F401  loads the top-level .env

import argparse
import os
import sys
import time
from pathlib import Path

from bson import json_util
from pymongo import ASCENDING, DESCENDING, MongoClient
from pymongo.errors import OperationFailure
from pymongo.operations import SearchIndexModel

ROOT = Path(__file__).resolve().parent.parent
VECTOR_INDEX = "claims_semantic"
EMBED_MODEL = "voyage-4"

VECTOR_DEFINITION = {
    "fields": [
        {"type": "autoEmbed", "modality": "text", "path": "loss_description", "model": EMBED_MODEL},
        {"type": "filter", "path": "peril"},
        {"type": "filter", "path": "status"},
        {"type": "filter", "path": "property_address.county"},
        {"type": "filter", "path": "property_address.city"},
        {"type": "filter", "path": "date_of_loss"},
    ]
}


def load(db, name: str) -> int:
    docs = json_util.loads((ROOT / "data" / f"{name}.json").read_text())
    db[name].drop()
    db[name].insert_many(docs)
    return len(docs)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-vector", action="store_true", help="skip the Atlas vector search index")
    args = ap.parse_args()

    uri = os.environ.get("MONGODB_URI")
    if not uri:
        sys.exit("Set MONGODB_URI first.")
    db = MongoClient(uri)[os.environ.get("MONGODB_DB", "contoso_claims")]

    print(f"claims:   {load(db, 'claims')} documents")
    print(f"policies: {load(db, 'policies')} documents")

    # Ordinary B-tree indexes for the find() and aggregate() prompts.
    db.claims.create_index([("policy_number", ASCENDING)])
    db.claims.create_index([("status", ASCENDING), ("assigned_adjuster", ASCENDING)])
    db.claims.create_index([("peril", ASCENDING), ("date_of_loss", DESCENDING)])
    db.claims.create_index([("contractor.name", ASCENDING)])
    db.claims.create_index([("cat_event.code", ASCENDING)])
    db.claims.create_index([("insured_name", ASCENDING)])
    print("b-tree indexes created")

    if args.no_vector:
        return

    try:
        db.claims.create_search_index(
            SearchIndexModel(definition=VECTOR_DEFINITION, name=VECTOR_INDEX, type="vectorSearch")
        )
    except OperationFailure as e:
        sys.exit(f"Could not create the vector index: {e}\n"
                 "Automated Embedding needs an Atlas cluster with it enabled. See README.md.")

    print(f"vector index '{VECTOR_INDEX}' requested; waiting for it to build", end="", flush=True)
    for _ in range(120):
        idx = next(iter(db.claims.list_search_indexes(VECTOR_INDEX)), None)
        if idx and idx.get("queryable"):
            print(" ready")
            return
        print(".", end="", flush=True)
        time.sleep(5)
    print("\nStill building after 10 minutes. Check the Atlas UI (Search & Vector Search tab).")


if __name__ == "__main__":
    main()

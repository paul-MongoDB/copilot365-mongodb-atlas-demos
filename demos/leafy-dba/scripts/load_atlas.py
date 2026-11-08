"""Create the isolated DBA fixture. --preview works offline; --reset reloads owned data."""
import argparse
import itertools
import sys

from _demo import (COLLECTION, COUNT, DATABASE, OPEN_PER_TENANT, OWNER, PLANTED_INDEXES, client,
                   documents, dump, run, state)


def load(db, reset=False):
    marker = state(db)
    exists = COLLECTION in db.list_collection_names()
    if marker and marker.get("owner") != OWNER:
        raise RuntimeError("The demo namespace has a different owner; refusing to overwrite it.")
    if exists:
        if not marker:
            raise RuntimeError("Collection already exists without the demo marker; refusing to overwrite it.")
        if not reset:
            raise RuntimeError("Fixture already exists. Use --reset to replace this demo's collection.")
        if db[COLLECTION].find_one({"_demo_owner": {"$ne": OWNER}}, {"_id": 1}):
            raise RuntimeError("Foreign documents found; refusing to reset the collection.")
    db["_demo_state"].update_one({"_id": COLLECTION}, {"$set": {"owner": OWNER, "ready": False}}, upsert=True)
    if exists:
        db[COLLECTION].drop()
    source = iter(documents())
    while batch := list(itertools.islice(source, 1000)):
        db[COLLECTION].insert_many(batch)
    for name, keys in PLANTED_INDEXES.items():
        db[COLLECTION].create_index(keys, name=name)
    db["_demo_state"].update_one({"_id": COLLECTION}, {"$set": {"ready": True, "count": COUNT}})
    print(f"Loaded {COUNT:,} synthetic documents into {DATABASE}.{COLLECTION}.")
    print(f"Baseline ready: _id_ plus planted indexes {', '.join(PLANTED_INDEXES)}.")
    print("Next: run run_workload.py so index usage and the profiler have real traffic.")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--preview", action="store_true", help="Print sample data without connecting")
    parser.add_argument("--reset", action="store_true", help="Replace only the owned fixture collection and its indexes")
    args = parser.parse_args()
    if args.preview:
        dump({"namespace": f"{DATABASE}.{COLLECTION}", "documents": COUNT,
              "tenant_042_open": OPEN_PER_TENANT, "sample": next(documents())})
        return
    with client() as connection:
        load(connection[DATABASE], args.reset)


if __name__ == "__main__":
    sys.exit(run(main))

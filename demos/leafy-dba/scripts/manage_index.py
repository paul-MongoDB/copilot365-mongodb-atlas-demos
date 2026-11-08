"""Presenter-only index change, scoped to leafy_dba.work_items."""
import argparse
import sys

from _demo import COLLECTION, DATABASE, INDEX, INDEX_KEYS, client, require_fixture, run


def change(db, undo=False):
    require_fixture(db)
    coll = db[COLLECTION]
    indexes = {i["name"]: i for i in coll.list_indexes()}
    existing = indexes.get(INDEX)
    if existing and list(existing["key"].items()) != INDEX_KEYS:
        raise RuntimeError("An index with the demo name has different keys; refusing to change it.")
    if undo:
        if existing:
            coll.drop_index(INDEX)
        print(f"Removed {INDEX} if present. Other indexes and documents were preserved.")
    else:
        coll.create_index(INDEX_KEYS, name=INDEX)
        print(f"Created {INDEX} on {DATABASE}.{COLLECTION}: {INDEX_KEYS}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--create", action="store_true", help="Build the compound index")
    group.add_argument("--undo", action="store_true", help="Drop only the named demo index")
    args = parser.parse_args()
    with client() as connection:
        change(connection[DATABASE], args.undo)


if __name__ == "__main__":
    sys.exit(run(main))

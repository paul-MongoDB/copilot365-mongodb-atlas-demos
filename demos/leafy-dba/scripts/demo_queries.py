"""Read-only inventory and query-plan evidence. Does not create indexes or load data."""
import argparse
import sys

from _demo import (BASELINE_INDEXES, COLLECTION, COUNT, DATABASE, FILTER, INDEX, INDEX_KEYS, LIMIT,
                   MAX_TIME_MS, OPEN_PER_TENANT, SORT, client, dump, explain, find_command,
                   require_fixture, run, summary)


def validate(db, result, phase):
    coll = db[COLLECTION]
    got = summary(result)
    indexes = {i["name"]: i for i in coll.list_indexes()}
    checks = {
        "fixture count": coll.count_documents({}, maxTimeMS=MAX_TIME_MS) == COUNT,
        "matching items": coll.count_documents(FILTER, maxTimeMS=MAX_TIME_MS) == OPEN_PER_TENANT,
        "returned items": got["nReturned"] == LIMIT,
    }
    if phase == "baseline":
        checks.update({"baseline indexes": set(indexes) == BASELINE_INDEXES,
                       "collection scan": "COLLSCAN" in got["winningStages"],
                       "blocking sort": "SORT" in got["winningStages"],
                       "full scan": got["totalDocsExamined"] == COUNT})
    else:
        checks.update({"planted indexes kept": BASELINE_INDEXES <= set(indexes),
                       "compound index": INDEX in indexes and list(indexes[INDEX]["key"].items()) == INDEX_KEYS,
                       "optimizer uses index": INDEX in got["indexesUsed"],
                       "no collection scan": "COLLSCAN" not in got["winningStages"],
                       "no blocking sort": "SORT" not in got["winningStages"],
                       "fewer documents examined": isinstance(got["totalDocsExamined"], int)
                       and got["totalDocsExamined"] <= LIMIT * 2})
    for name, ok in checks.items():
        print(f"{'PASS' if ok else 'FAIL'}: {name}")
    return 0 if all(checks.values()) else 1


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Exit 1 if fixture or plan differs from the selected phase")
    parser.add_argument("--phase", choices=("baseline", "indexed"), default="baseline",
                        help="Expected state for --check (default baseline)")
    parser.add_argument("--explain", action="store_true", help="Also print the complete explain result")
    args = parser.parse_args()
    with client() as connection:
        db = connection[DATABASE]
        require_fixture(db)
        print(f"Namespace: {DATABASE}.{COLLECTION}")
        print("Collection inventory (including the fixture marker):")
        dump(db.list_collection_names())
        print("Database statistics, in bytes:")
        stats = db.command("dbStats")
        dump({key: stats.get(key) for key in ("collections", "objects", "dataSize", "storageSize", "indexes", "indexSize")})
        print("B-tree indexes:")
        dump(list(db[COLLECTION].list_indexes()))
        print("Query being explained, no hint:")
        dump(find_command())
        result = explain(db)
        print("Execution evidence (timing varies; compare examined documents and plan stages):")
        dump(summary(result))
        print("First three matching items:")
        dump(list(db[COLLECTION].find(FILTER, {"tenant_id": 1, "status": 1, "created_at": 1})
                  .sort(list(SORT.items())).limit(3).max_time_ms(MAX_TIME_MS)))
        if args.explain:
            dump(result)
        if args.check:
            return validate(db, result, args.phase)


if __name__ == "__main__":
    sys.exit(run(main))

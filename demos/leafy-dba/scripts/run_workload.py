"""Run a realistic application workload against the fixture, with the database profiler on.

Run it after load_atlas.py and before presenting. It gives $indexStats real usage counters and
fills leafy_dba.system.profile with the inefficient operations, so Copilot can answer "which
indexes should I add or remove?" from evidence. Reads only: it never writes to work_items.

The profiler is switched on for this database only, records only operations that read 100 or
more documents or sort in memory, and is switched off again when the run ends. Its records stay
in system.profile, a capped 16 MB collection, until the next run.
"""
import argparse
import collections
import concurrent.futures
import datetime as dt
import random
import sys
import threading
import time

from _demo import (COLLECTION, COUNT, DATABASE, MAX_TIME_MS, PROFILE_FILTER, REDUNDANT_INDEX, SERVICES,
                   START, STATUSES, TENANTS, UNUSED_INDEX, USED_INDEX, client, require_fixture, run)

PROFILE_BYTES = 16 * 1024 * 1024


def tenant_queue(coll, rng):
    """The worker's main screen: newest 20 items in one tenant's queue. No index fits it."""
    return list(coll.find({"tenant_id": f"tenant-{rng.randrange(TENANTS):03d}", "status": rng.choice(STATUSES)})
                .sort("created_at", -1).limit(20).max_time_ms(MAX_TIME_MS))


def retry_scan(coll, rng):
    """Retry job: items in one service that failed twice or more. Served by service_1_attempts_1."""
    return list(coll.find({"service": rng.choice(SERVICES), "attempts": {"$gte": 2}},
                          {"_id": 1, "attempts": 1}).limit(50).max_time_ms(MAX_TIME_MS))


def daily_report(coll, rng):
    """Daily report: every item created on one day. No index on created_at alone."""
    day = START + dt.timedelta(days=rng.randrange(20))
    return list(coll.find({"created_at": {"$gte": day, "$lt": day + dt.timedelta(days=1)}},
                          {"_id": 1, "status": 1}).batch_size(5000).max_time_ms(MAX_TIME_MS))


def item_lookup(coll, rng):
    """Detail page: one item by _id. Always efficient."""
    return coll.find_one({"_id": rng.randrange(COUNT)}, max_time_ms=MAX_TIME_MS)


# Weights are rough shares of traffic: the queue screen dominates, the report is occasional.
SHAPES = [(tenant_queue, 45), (retry_scan, 35), (daily_report, 5), (item_lookup, 15)]


def worker(coll, seed, deadline, counts, lock):
    rng = random.Random(seed)
    functions, weights = zip(*SHAPES)
    local = collections.Counter()
    while time.monotonic() < deadline:
        shape = rng.choices(functions, weights)[0]
        shape(coll, rng)
        local[shape.__name__] += 1
    with lock:
        counts.update(local)


def profiler_off(db):
    # Level 0 alone keeps the filter, which would still change slow-query logging. Unset it.
    db.command({"profile": 0, "filter": "unset"})


def start_profiler(db):
    profiler_off(db)
    db["system.profile"].drop()  # start each run with a clean record
    # The default 1 MB holds only the newest few hundred records. 16 MB holds a full run.
    db.create_collection("system.profile", capped=True, size=PROFILE_BYTES)
    db.command({"profile": 1, "filter": PROFILE_FILTER})


def report(db, counts, seconds):
    coll = db[COLLECTION]
    total = sum(counts.values())
    print(f"Ran {total:,} queries in {seconds:.0f} seconds:")
    for shape, _ in SHAPES:
        print(f"  {shape.__name__:13} {counts[shape.__name__]:6,}")
    print("\nProfiler records, grouped by query shape:")
    shapes = list(db["system.profile"].aggregate([
        {"$match": {"ns": f"{DATABASE}.{COLLECTION}", "op": "query"}},
        {"$group": {"_id": "$queryHash", "count": {"$sum": 1}, "plan": {"$first": "$planSummary"},
                    "filter": {"$first": "$command.filter"}, "sort": {"$first": "$command.sort"},
                    "avgMillis": {"$avg": "$millis"}, "avgDocsExamined": {"$avg": "$docsExamined"},
                    "avgReturned": {"$avg": "$nreturned"}, "inMemorySort": {"$max": "$hasSortStage"}}},
        {"$sort": {"count": -1}}]))
    for s in shapes:
        fields = ", ".join(s["filter"] or {})
        print(f"  {s['count']:4} x {s['plan']:9} filter on {fields}; sort {dict(s['sort'] or {})}; "
              f"avg {s['avgMillis']:.0f} ms, {s['avgDocsExamined']:,.0f} docs read, "
              f"{s['avgReturned']:,.0f} returned, in-memory sort {bool(s['inMemorySort'])}")
    print("\nIndex usage since each index was built ($indexStats, this node only):")
    usage = {s["name"]: s["accesses"]["ops"] for s in coll.aggregate([{"$indexStats": {}}])}
    for name, ops in sorted(usage.items()):
        print(f"  {name:22} {ops:8,}")
    level = db.command("profile", -1)
    checks = {
        "profiler caught the tenant queue scan": any(
            s["plan"] == "COLLSCAN" and set(s["filter"] or {}) == {"tenant_id", "status"} for s in shapes),
        "profiler caught the daily report scan": any(
            s["plan"] == "COLLSCAN" and set(s["filter"] or {}) == {"created_at"} for s in shapes),
        f"{USED_INDEX} was used": usage.get(USED_INDEX, 0) > 0,
        f"{UNUSED_INDEX} was never used": usage.get(UNUSED_INDEX) == 0,
        f"{REDUNDANT_INDEX} was never used": usage.get(REDUNDANT_INDEX) == 0,
        "profiler is off and its filter is unset": level.get("was") == 0 and not level.get("filter"),
    }
    print()
    for name, ok in checks.items():
        print(f"{'PASS' if ok else 'FAIL'}: {name}")
    return 0 if all(checks.values()) else 1


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--seconds", type=float, default=60, help="How long to run (default 60)")
    parser.add_argument("--threads", type=int, default=8, help="Parallel clients (default 8)")
    args = parser.parse_args()
    with client() as connection:
        db = connection[DATABASE]
        require_fixture(db)
        start_profiler(db)
        counts, lock = collections.Counter(), threading.Lock()
        began = time.monotonic()
        try:
            with concurrent.futures.ThreadPoolExecutor(args.threads) as pool:
                futures = [pool.submit(worker, db[COLLECTION], seed, began + args.seconds, counts, lock)
                           for seed in range(args.threads)]
                for future in futures:
                    future.result()
        finally:
            profiler_off(db)
        return report(db, counts, time.monotonic() - began)


if __name__ == "__main__":
    sys.exit(run(main))

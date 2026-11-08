"""Shared fixture and query definition for the Leafy DBA demo."""
from __future__ import annotations

import datetime as dt
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "common"))
import _env  # noqa: F401
from bson import json_util
from pymongo import MongoClient
from pymongo.errors import PyMongoError

DATABASE = os.environ.get("MONGODB_DB_DBA", "leafy_dba")
COLLECTION = "work_items"
OWNER = "copilot365-atlas-demo/leafy-dba/v1"
COUNT = 30_000
TENANTS = 100
OPEN_PER_TENANT = 75
START = dt.datetime(2026, 10, 1)
STATUSES = ("open", "running", "complete", "failed")
SERVICES = ("ingestion", "reporting", "sync")
INDEX = "tenant_status_created"
INDEX_KEYS = [("tenant_id", 1), ("status", 1), ("created_at", -1)]
FILTER = {"tenant_id": "tenant-042", "status": "open"}
SORT = {"created_at": -1}
LIMIT = 20
MAX_TIME_MS = 10_000

# Indexes the loader plants so the audience can ask which ones to keep and which to remove.
# service_1 is redundant: service_1_attempts_1 starts with the same key, so it serves every
# query service_1 could. description_1 is unused: no query filters or sorts on description,
# and every document has the same value. service_1_attempts_1 is the one the workload uses.
REDUNDANT_INDEX = "service_1"
UNUSED_INDEX = "description_1"
USED_INDEX = "service_1_attempts_1"
PLANTED_INDEXES = {
    REDUNDANT_INDEX: [("service", 1)],
    USED_INDEX: [("service", 1), ("attempts", 1)],
    UNUSED_INDEX: [("description", 1)],
}
BASELINE_INDEXES = {"_id_", *PLANTED_INDEXES}

# The profiler records only inefficient operations: many documents read, or an in-memory sort.
PROFILE_FILTER = {"$or": [{"docsExamined": {"$gte": 100}}, {"hasSortStage": True}]}


def documents():
    """300 items per tenant, 75 open. Timestamps are unique and reproducible."""
    for n in range(COUNT):
        yield {
            "_id": n,
            "_demo_owner": OWNER,
            "tenant_id": f"tenant-{n % TENANTS:03d}",
            "status": STATUSES[(n // 100) % 4],
            "created_at": START + dt.timedelta(minutes=n),
            "service": SERVICES[(n // 400) % 3],
            "attempts": (n // 400) % 4,
            "description": "Synthetic work item for a query tuning demonstration.",
        }


def client():
    uri = os.environ.get("MONGODB_URI")
    if not uri:
        raise RuntimeError("Set MONGODB_URI in the root .env or environment first.")
    return MongoClient(uri, serverSelectionTimeoutMS=10_000, connectTimeoutMS=10_000,
                       appname="copilot365-leafy-dba-demo")


def state(db):
    return db["_demo_state"].find_one({"_id": COLLECTION})


def require_fixture(db):
    marker = state(db)
    if not marker or marker.get("owner") != OWNER or not marker.get("ready"):
        raise RuntimeError("Leafy DBA fixture is not ready. Run load_atlas.py first.")
    if db[COLLECTION].find_one({"_demo_owner": {"$ne": OWNER}}, {"_id": 1}):
        raise RuntimeError("Foreign documents found in the demo collection; refusing to continue.")


def find_command():
    return {"find": COLLECTION, "filter": FILTER, "sort": SORT, "limit": LIMIT,
            "maxTimeMS": MAX_TIME_MS}


def explain(db):
    # No hint: show the optimizer's actual choice before and after the index exists.
    return db.command({"explain": find_command(), "verbosity": "executionStats"})


def plan_details(value):
    """Handle classic, slot-based and nested shard plan structures."""
    stages, indexes = set(), set()

    def visit(node):
        if isinstance(node, dict):
            if isinstance(node.get("stage"), str):
                stages.add(node["stage"])
            if isinstance(node.get("indexName"), str):
                indexes.add(node["indexName"])
            for key, child in node.items():
                if key not in {"rejectedPlans", "allPlansExecution"}:
                    visit(child)
        elif isinstance(node, list):
            for child in node:
                visit(child)

    visit(value)
    return sorted(stages), sorted(indexes)


def summary(result):
    # Rejected plans must not be mistaken for stages used by the winning plan.
    stages, indexes = plan_details(result.get("queryPlanner", {}).get("winningPlan", {}))
    stats = result.get("executionStats", {})
    return {"winningStages": stages, "indexesUsed": indexes,
            **{key: stats.get(key) for key in (
                "nReturned", "totalDocsExamined", "totalKeysExamined", "executionTimeMillis")}}


def dump(value):
    print(json_util.dumps(value, indent=2))


def run(main):
    try:
        return main() or 0
    except RuntimeError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    except PyMongoError as exc:
        # Driver error text can contain connection details. Report only type and server code.
        code = getattr(exc, "code", None)
        print(f"MongoDB operation failed ({type(exc).__name__}, code={code}). "
              "Check connectivity and demo-user permissions.", file=sys.stderr)
        return 1

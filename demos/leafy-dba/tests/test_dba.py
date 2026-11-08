"""Offline unit tests and integration against a disposable loopback-only mongod."""
import contextlib
import io
import os
from pathlib import Path
import shutil
import socket
import subprocess
import sys
import tempfile
import time
import unittest

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))
from _demo import (BASELINE_INDEXES, COLLECTION, COUNT, DATABASE, FILTER, INDEX, LIMIT, OWNER,
                   PLANTED_INDEXES, REDUNDANT_INDEX, SORT, USED_INDEX, documents, explain,
                   require_fixture, summary)
from load_atlas import load
from manage_index import change
from pymongo import MongoClient
from pymongo.errors import PyMongoError


class FixtureTests(unittest.TestCase):
    def test_distribution_and_stable_order(self):
        rows = list(documents())
        self.assertEqual(len(rows), COUNT)
        self.assertEqual(len({r["_id"] for r in rows}), COUNT)
        self.assertEqual(len({r["created_at"] for r in rows}), COUNT)
        self.assertEqual(len({r["tenant_id"] for r in rows}), 100)
        matches = [r for r in rows if all(r[k] == v for k, v in FILTER.items())]
        self.assertEqual(len(matches), 75)
        self.assertEqual(rows, list(documents()))

    def test_rejected_plans_are_not_reported_as_used(self):
        result = {"queryPlanner": {
            "winningPlan": {"queryPlan": {"stage": "FETCH", "inputStage": {
                "stage": "IXSCAN", "indexName": INDEX}}},
            "rejectedPlans": [{"stage": "COLLSCAN"}]},
            "executionStats": {"nReturned": 20, "totalDocsExamined": 20}}
        got = summary(result)
        self.assertEqual(got["winningStages"], ["FETCH", "IXSCAN"])
        self.assertEqual(got["indexesUsed"], [INDEX])
        self.assertIsNone(got["totalKeysExamined"])

    def test_nested_shard_rejections_are_excluded(self):
        result = {"queryPlanner": {"winningPlan": {"stage": "SHARD_MERGE", "shards": [{
            "winningPlan": {"stage": "IXSCAN", "indexName": INDEX},
            "rejectedPlans": [{"stage": "SORT", "inputStage": {"stage": "COLLSCAN"}}]}]}}}
        got = summary(result)
        self.assertEqual(got["winningStages"], ["IXSCAN", "SHARD_MERGE"])

    def test_preview_runs_without_database_access(self):
        env = dict(os.environ, MONGODB_URI="mongodb://127.0.0.1:1/")
        result = subprocess.run([sys.executable, str(SCRIPTS / "load_atlas.py"), "--preview"],
                                env=env, capture_output=True, text=True, timeout=10)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('"documents": 30000', result.stdout)


@unittest.skipUnless(shutil.which("mongod"), "mongod not installed; local integration skipped")
class LocalMongoTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory(prefix="leafy-dba-test-")
        cls.addClassCleanup(cls.temp.cleanup)
        with socket.socket() as sock:
            sock.bind(("127.0.0.1", 0))
            port = sock.getsockname()[1]
        cls.uri = f"mongodb://127.0.0.1:{port}/"
        cls.proc = subprocess.Popen([
            shutil.which("mongod"), "--dbpath", cls.temp.name, "--bind_ip", "127.0.0.1",
            "--port", str(port), "--nounixsocket", "--logpath", str(Path(cls.temp.name) / "mongod.log")],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        cls.addClassCleanup(cls.stop_server)
        cls.connection = MongoClient(cls.uri, serverSelectionTimeoutMS=200)
        cls.addClassCleanup(cls.connection.close)
        for _ in range(100):
            if cls.proc.poll() is not None:
                raise RuntimeError("Temporary mongod failed to start; inspect its installed runtime.")
            try:
                cls.connection.admin.command("ping")
                break
            except PyMongoError:
                time.sleep(0.1)
        else:
            raise RuntimeError("Temporary mongod did not become ready.")

    @classmethod
    def stop_server(cls):
        if cls.proc.poll() is None:
            cls.proc.terminate()
            try:
                cls.proc.wait(timeout=10)
            except subprocess.TimeoutExpired:
                cls.proc.kill()
                cls.proc.wait(timeout=5)

    def setUp(self):
        # This client is created above, always against our private temporary local server.
        self.connection.drop_database(DATABASE)
        self.db = self.connection[DATABASE]

    def quiet(self, func, *args, **kwargs):
        with contextlib.redirect_stdout(io.StringIO()):
            return func(*args, **kwargs)

    def cli(self, filename, *args, expected=0):
        env = dict(os.environ, MONGODB_URI=self.uri)
        result = subprocess.run([sys.executable, str(SCRIPTS / filename), *args], env=env,
                                capture_output=True, text=True, timeout=30)
        self.assertEqual(result.returncode, expected, result.stdout + result.stderr)
        return result.stdout

    def results(self):
        return list(self.db[COLLECTION].find(FILTER).sort(list(SORT.items())).limit(LIMIT))

    def test_full_cli_rehearsal_and_read_only_queries(self):
        self.cli("load_atlas.py")
        before_docs = self.results()
        before_indexes = list(self.db[COLLECTION].list_indexes())
        self.cli("demo_queries.py", "--check", "--phase", "baseline", "--explain")
        self.assertEqual(before_docs, self.results())
        self.assertEqual(before_indexes, list(self.db[COLLECTION].list_indexes()))
        self.cli("manage_index.py", "--create")
        self.cli("manage_index.py", "--create")  # repeated creation is harmless
        self.cli("demo_queries.py", "--check", "--phase", "indexed")
        self.assertEqual(before_docs, self.results())
        self.cli("demo_queries.py", "--check", "--phase", "baseline", expected=1)
        self.cli("manage_index.py", "--undo")
        self.cli("manage_index.py", "--undo")
        self.cli("demo_queries.py", "--check", "--phase", "baseline")

    def test_loader_plants_redundant_and_unused_indexes(self):
        self.quiet(load, self.db)
        names = set(self.db[COLLECTION].index_information())
        self.assertEqual(names, BASELINE_INDEXES)
        # The redundant index really is a prefix of the index the workload uses.
        self.assertEqual(PLANTED_INDEXES[USED_INDEX][:1], PLANTED_INDEXES[REDUNDANT_INDEX])

    def test_workload_leaves_evidence_and_turns_profiler_off(self):
        self.cli("load_atlas.py")
        before = self.results()
        out = self.cli("run_workload.py", "--seconds", "3", "--threads", "4")
        self.assertNotIn("FAIL", out)
        self.assertEqual(before, self.results())
        level = self.db.command("profile", -1)
        self.assertEqual(level["was"], 0)
        self.assertNotIn("filter", level)
        self.assertGreater(self.db["system.profile"].count_documents({}), 0)
        # The workload changes no data or indexes, so the opening state still checks out.
        self.cli("demo_queries.py", "--check", "--phase", "baseline")

    def test_unowned_collection_is_never_replaced(self):
        self.db[COLLECTION].insert_one({"_id": "keep", "important": True})
        for reset in (False, True):
            with self.assertRaisesRegex(RuntimeError, "without the demo marker"):
                load(self.db, reset)
        self.assertTrue(self.db[COLLECTION].find_one({"_id": "keep"})["important"])

    def test_foreign_documents_block_reset_and_index_change(self):
        self.quiet(load, self.db)
        self.db[COLLECTION].insert_one({"_id": "foreign"})
        with self.assertRaisesRegex(RuntimeError, "Foreign documents"):
            load(self.db, reset=True)
        with self.assertRaisesRegex(RuntimeError, "Foreign documents"):
            change(self.db)
        self.assertEqual(self.db[COLLECTION].count_documents({}), COUNT + 1)

    def test_reset_preserves_other_demo_data(self):
        self.quiet(load, self.db)
        self.quiet(change, self.db)
        self.db.other_collection.insert_one({"_id": "keep"})
        self.connection.leafy_tech.sentinel.insert_one({"_id": "keep"})
        with self.assertRaisesRegex(RuntimeError, "already exists"):
            load(self.db)
        self.quiet(load, self.db, reset=True)
        got = summary(explain(self.db))
        self.assertIn("COLLSCAN", got["winningStages"])
        self.assertEqual(self.db[COLLECTION].count_documents({}), COUNT)
        self.assertIsNotNone(self.db.other_collection.find_one({"_id": "keep"}))
        self.assertIsNotNone(self.connection.leafy_tech.sentinel.find_one({"_id": "keep"}))

    def test_incomplete_fixture_cannot_be_presented(self):
        self.db["_demo_state"].insert_one({"_id": COLLECTION, "owner": OWNER, "ready": False})
        with self.assertRaisesRegex(RuntimeError, "not ready"):
            require_fixture(self.db)

    def test_same_index_name_with_different_keys_is_preserved(self):
        self.quiet(load, self.db)
        self.db[COLLECTION].create_index([("attempts", -1)], name=INDEX)
        for undo in (False, True):
            with self.assertRaisesRegex(RuntimeError, "different keys"):
                change(self.db, undo)
        self.assertEqual(self.db[COLLECTION].index_information()[INDEX]["key"], [("attempts", -1)])


if __name__ == "__main__":
    unittest.main()

# Leafy DBA: inspect, clean up, diagnose, verify

A 15-minute operations demo for DBAs and platform engineers. Start with their Atlas projects
and clusters, inspect database structure and indexes, find indexes to remove from their usage
counters, read the database profiler to find slow queries, then explain the worst query before
and after adding a compound index. No business storyline or Microsoft 365 content seeding is
required.

Presenter walkthrough: [DEMO_SCRIPT.md](DEMO_SCRIPT.md). Copy-and-paste questions:
[stage/prompts.txt](stage/prompts.txt). Use this category when the audience asks about operating
MongoDB rather than a sales, claims or movie workflow.

## What is live and what is synthetic

Project and cluster discovery uses the signed-in presenter's actual Atlas inventory. Choose
a demo project before presenting and scope subsequent questions to it. Cluster configuration
is not evidence of runtime health. Do not treat an `IDLE` state as proof that a workload is healthy.

The query tuning exercise uses **30,000 synthetic documents** in `leafy_dba.work_items` on a
dedicated sandbox cluster. Each of 100 tenants has 300 items, including 75 with status `open`.
The query returns the newest 20 open items for `tenant-042`. A marker collection, `_demo_state`,
tracks whether setup completed. No project, cluster, database user or paid resource is created.

The loader also plants three indexes, so there is something to clean up:

| Index | Role in the demo |
|---|---|
| `service_1_attempts_1` | Used by the workload's retry job. Keep. |
| `service_1` | Redundant: `service_1_attempts_1` starts with the same key. Never used. |
| `description_1` | Never used. Every document has the same description. |

`run_workload.py` then plays 60 seconds of application traffic from 8 parallel clients: the
tenant queue query (no index fits it), the retry job, a daily report on a `created_at` range
(no index fits it either) and lookups by `_id`. It reads only. While it runs, the database
profiler is on for `leafy_dba` alone and records operations that read 100 or more documents
or sort in memory. It is turned off, and its filter removed, when the run ends. The records
stay in `leafy_dba.system.profile`, a capped 16 MB collection, for Copilot to read. The same
operations also appear in the server log as slow-query lines while the profiler is on.

The usage counters and profiler records are real measurements of synthetic traffic. Usage
counters reset when the cluster restarts, so run the workload within a few hours of
presenting. The database user needs permission to run the `profile` command on `leafy_dba`
(the `dbAdmin` role on that database covers it).

## Prepare the sandbox

Use the root Python environment and `MONGODB_URI` from the [shared setup](../../README.md).
The URI should point to a dedicated sandbox and a database user allowed to read, write and
manage indexes in `leafy_dba`. The Python scripts use that database user; Copilot uses the
signed-in Atlas user's delegated access. Verify both reach the same cluster.

Run from the repository root:

```bash
# Offline sample and expected counts. Does not connect to MongoDB.
.venv/bin/python demos/leafy-dba/scripts/load_atlas.py --preview

# Initial setup. Creates only the fixture, its planted indexes and its ownership marker.
.venv/bin/python demos/leafy-dba/scripts/load_atlas.py
.venv/bin/python demos/leafy-dba/scripts/demo_queries.py --check --phase baseline

# Play 60 seconds of traffic with the profiler on. Prints PASS lines for the evidence.
.venv/bin/python demos/leafy-dba/scripts/run_workload.py

# Rehearse the on-stage change and verify it.
.venv/bin/python demos/leafy-dba/scripts/manage_index.py --create
.venv/bin/python demos/leafy-dba/scripts/demo_queries.py --check --phase indexed

# Restore the opening state after rehearsal.
.venv/bin/python demos/leafy-dba/scripts/manage_index.py --undo
.venv/bin/python demos/leafy-dba/scripts/demo_queries.py --check --phase baseline
```

`load_atlas.py` refuses to overwrite an existing collection by default. To regenerate this
demo's fixture, use `--reset`; this replaces `work_items` and all its indexes, and recreates
the planted ones. It requires the
ownership marker and refuses if any document has a different owner. It never drops a database
or touches the other demos. `manage_index.py --undo` removes only `tenant_status_created`.
Do not run a reset while presenting or against a shared production workload.

## Rehearse the connector separately

1. Enable the Atlas source in Copilot and confirm the sign-in. Use a model that successfully
   calls the connector in your rehearsal. Open one new conversation per run.
2. Keep organization AI client access in **Read** mode. Index changes are made by the presenter
   through the terminal script, so this demo needs no AI write access.
3. Run prompt 1. Record the chosen project name, project ID and sandbox cluster name in your
   presenter notes. Replace `<PROJECT_ID>` and `<CLUSTER_NAME>` in the stage prompts.
4. Rehearse prompts 2 through 7 on that cluster. Confirm the source actually exposes inventory,
   collection indexes, `aggregate` (for `$indexStats` and `system.profile`) and `explain` with
   `executionStats`; tool availability can vary by client,
   connector setup and permissions. Tools visible in another AI client do not prove Copilot has them.
5. If discovery is unavailable, open the Atlas project's Clusters view and identify the sandbox
   there. Continue with the database prompts if those work. If `explain` is unavailable, use
   `demo_queries.py --explain` and label it as a direct database query from the terminal.

A database connection string alone does not provide the Atlas Administration API inventory.
For this demo, Copilot supplies project/cluster discovery; Python supplies database verification.
With a self-managed MCP deployment, Atlas tools require separate Atlas API configuration.
Use a role scoped to the demo project and rehearse the actual inventory permissions.

## Expected evidence

| Point | Initial state | After presenter creates the index |
|---|---|---|
| Documents | 30,000 | 30,000 |
| Matching open items for tenant-042 | 75 | 75 |
| Query result limit | 20 | 20 |
| Indexes | `_id_` plus the three planted indexes | The same, plus `tenant_status_created` |
| Winning plan | Collection scan and blocking sort | Uses the compound index, no blocking sort |
| Documents examined | 30,000 | Typically 20; check permits up to 40 |

Neither query is hinted. The comparison shows the optimizer choosing a different plan after
the index is added. Use examined documents, examined keys and plan stages as the evidence;
milliseconds on a small dataset vary with cache and load. This is not a production benchmark.
The index supports equality on `tenant_id` and `status`, followed by descending `created_at`.
It is not a covered query because the query returns complete documents.

## Optional Q&A

See the walkthrough for the slow query log, alerts, Performance Advisor, backup and access
questions. Those beats depend on the cluster's tier, configuration, privileges and the tools
available in the presenting client. Empty recommendations are an acceptable answer. Setup
creates no incidents, backup status or Atlas health metrics. The only slow-query evidence is
what the workload's real queries produce.

## Verification

```bash
.venv/bin/python -m unittest discover -s demos/leafy-dba/tests -v
```

Unit tests run offline. Integration tests start a temporary local `mongod` when installed,
exercise loading, explaining, creating and undoing the index, and check overwrite protection.
They never use the root `.env` connection. Without `mongod`, integration tests are skipped;
the two `--check` commands still need to pass on your Atlas sandbox before presenting.

## References

- [MongoDB MCP tools](https://www.mongodb.com/docs/mcp-server/tools/): inventory, inspection and explain capabilities.
- [AI client access](https://www.mongodb.com/docs/mcp-server/remote-mcp/manage-ai-client-access/): delegated roles and Read mode.
- [Explain](https://www.mongodb.com/docs/manual/reference/command/explain/): execution evidence.
- [Equality, Sort, Range guideline](https://www.mongodb.com/docs/manual/tutorial/equality-sort-range-guideline/): index field order.
- [Index usage statistics](https://www.mongodb.com/docs/manual/reference/operator/aggregation/indexstats/): node-local counters and their reset behavior.

Documentation checked November 6, 2026. Copilot prompts still require a live rehearsal.

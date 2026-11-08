# Leafy DBA, a 15-minute demo: inspect, clean up, diagnose, verify

**Audience:** DBAs, database engineers and platform teams.

**Takeaway:** ask the questions a DBA asks every week in plain language: which indexes can I
drop, what is slow, what index fixes it. Then check the evidence, make a controlled change and
measure that the query does less work.

**The setup in one paragraph:** `leafy_dba.work_items` holds 30,000 synthetic queue items. It
ships with three indexes a real team might have left behind: one that is used, one that is
redundant and one that nobody uses. A workload script plays a minute of application traffic
with the database profiler on, so the usage counters and the profiler hold real evidence. The
main query has no index that fits it, and fixing that is the on-stage change.

## Before the audience arrives

Within a few hours of presenting (a cluster restart resets the usage counters), run:

```bash
.venv/bin/python demos/leafy-dba/scripts/load_atlas.py --reset
.venv/bin/python demos/leafy-dba/scripts/run_workload.py
.venv/bin/python demos/leafy-dba/scripts/demo_queries.py --check --phase baseline
```

The workload prints its own PASS lines and turns the profiler off when it finishes. Every
check must say PASS.

- Open Copilot Chat with the Atlas source signed in and a rehearsed tool-capable model.
- In the prompts below, replace `<PROJECT_ID>` and `<CLUSTER_NAME>` with the sandbox values from
  rehearsal. Or copy `stage/prompts.txt` to `stage/prompts.local.txt`, which git ignores, fill
  the values in once and paste from there.
- Open a terminal at the repository root and enlarge its font. Keep the workload output in
  the scrollback: it is your fallback for prompts 4 and 5.
- Open the sandbox project's Atlas Clusters page as a fallback for inventory questions.
- Confirm Copilot and `MONGODB_URI` reach the same sandbox. Keep credentials off screen.
- No Teams posts, OneDrive files, vector index, embeddings or new cluster are needed.

## 0:00 Discover the environment

Say: "Let's start where a DBA starts: what projects and clusters can I see?"

Paste prompt 1:

```text
Use the MongoDB Atlas source to list the projects my signed-in account can access. Show each project's name and ID. Retrieve remaining pages if supported; otherwise say the list is partial. Use returned inventory, not examples. Do not make changes or show connection strings. Keep all operations read-only throughout this conversation.
```

Pick the sandbox project by its ID. Then paste prompt 2:

```text
For Atlas project <PROJECT_ID>, list the clusters, then inspect <CLUSTER_NAME>. Show the cloud provider, region, tier, MongoDB version, paused status and configuration state where the tools return them. Mark unavailable fields as unknown. Keep connection strings out of the answer. Distinguish configuration from runtime health and say which tool supplied each fact.
```

Show: actual names and IDs, then provider, region, tier, MongoDB version and cluster state.
A missing field should stay unknown. This is configuration, not a health check.

If a tool is missing, say: "This connector session doesn't expose that operation. Here is the
same project in Atlas." Open the project, then return to Copilot for database work.

## 2:30 Inspect the database

Paste prompt 3:

```text
Connect to <CLUSTER_NAME> in project <PROJECT_ID>. Inspect database leafy_dba. List its collections. For work_items, show the document count, sampled schema, storage information if available, and every B-tree index with its key order and options. Clearly label sampled or estimated information. Do not infer that no Search indexes exist merely from a B-tree index listing. The _demo_state collection is a setup marker.
```

Expect 30,000 documents and four indexes: `_id_`, `service_1`, `service_1_attempts_1` and
`description_1`.

Say: "Four indexes. Every one of them costs disk, memory and time on every write. Are they all
earning their keep?"

## 4:00 Which indexes can I remove?

Paste prompt 4:

```text
For leafy_dba.work_items, are there any indexes I should remove? Use the index definitions and the $indexStats usage counters, including accesses.ops and accesses.since. Look for indexes that are never used and indexes made redundant by another index with the same leading keys. For each index say keep, remove or review, with the evidence. Then explain how to remove one safely. Do not change anything.
```

Expect:

| Index | Uses | Verdict | Why |
|---|---:|---|---|
| `description_1` | 0 | Remove | Never used. Every document has the same description, so it narrows nothing. |
| `service_1` | 0 | Remove | Never used, and redundant: `service_1_attempts_1` starts with `service`. |
| `service_1_attempts_1` | about 3,000 | Keep | The retry job uses it on every run. |
| `_id_` | some | Keep | Required. |

A strong answer adds two cautions, and if Copilot skips them, say them yourself. First, hide
the index before dropping it: a hidden index is ignored by queries but still maintained, so
unhiding it is instant if something slows down. Second, these counters are per node and reset
on restart, so check every node over a full business cycle (month-end jobs included) before
dropping anything in production.

Say: "That's two indexes we're paying for on every write and never reading. And it showed me
the evidence, not a guess."

Fallback: the workload output in the terminal shows the same usage counts.

## 6:30 What is slow? Read the profiler

Say: "Now the other direction. What's missing? The profiler has been recording every
operation that read 100 or more documents or sorted in memory."

Paste prompt 5:

```text
The database profiler has been recording inefficient operations in leafy_dba. Read the system.profile collection and group the operations on work_items by query shape. For each shape show the filter fields, sort, number of runs, average milliseconds, average documents examined, average documents returned, plan summary and whether it sorted in memory. Then recommend the indexes that would fix them, with exact key order, following the equality, sort, range guideline. Do not create anything.
```

Expect two query shapes:

| Shape | Runs | Plan | Read vs returned | In-memory sort | Fix |
|---|---:|---|---|---|---|
| `tenant_id` + `status`, newest first | about 4,100 | COLLSCAN | 30,000 for 20 | Yes | `{tenant_id: 1, status: 1, created_at: -1}` |
| `created_at` range (daily report) | about 490 | COLLSCAN | 30,000 for 1,440 | No | `{created_at: 1}` |

Say: "The queue screen runs thousands of times and reads the whole collection every time to
return 20 items. That's the one to fix first."

If Copilot says it can't read `system.profile`, move on to prompt 6. The workload output in
the terminal has the same table.

## 9:00 Explain the worst query

Paste prompt 6:

```text
In leafy_dba.work_items on that same cluster, run explain with executionStats for find({tenant_id: "tenant-042", status: "open"}).sort({created_at: -1}).limit(20). Return complete documents, with no projection and no hint. Show the exact query, winning plan stages, index used if any, nReturned, totalDocsExamined, totalKeysExamined and executionTimeMillis. Preserve these figures as our baseline. Then show the createIndex command, named tenant_status_created, that would fix it, for review only. Do not execute it or any other write.
```

Expect 20 returned, 30,000 documents examined, a collection scan and a blocking sort. Keep
this answer visible for comparison. The proposed index is:

```javascript
{tenant_id: 1, status: 1, created_at: -1}
```

Why that order: equality on tenant and status first, then the sort field, so the index returns
items already in order. It costs storage and a little time on every write. It is not a covered
query, because the query returns complete documents.

Terminal fallback, also useful to show the full server output:

```bash
.venv/bin/python demos/leafy-dba/scripts/demo_queries.py --check --phase baseline --explain
```

## 10:30 Make the change

Say: "Copilot proposed it. I apply it through a scoped script, and the AI connection stays
read-only."

```bash
.venv/bin/python demos/leafy-dba/scripts/manage_index.py --create
```

Wait for the script to return successfully. It changes only this demo's named index. If the
build fails, read the terminal result rather than narrating an improvement that didn't happen.

## 11:00 Verify, using the same query

Paste prompt 7:

```text
I created the index through a separate presenter script. Fetch the current indexes again, and run a fresh explain with executionStats for exactly the same find query, sort, limit, no projection and no hint from prompt 6. Compare the actual before and after winning plan, index used, nReturned, totalDocsExamined and totalKeysExamined in a table. Is the blocking sort gone? Use actual returned figures and mark any missing baseline values as unknown. Treat elapsed time as variable, not a production performance guarantee.
```

Expect `tenant_status_created` in the plan, no blocking sort, and 20 documents examined for
the same 20 returned.

```bash
.venv/bin/python demos/leafy-dba/scripts/demo_queries.py --check --phase indexed
```

Say: "From 30,000 documents read to 20, for the same answer. That's the number a DBA cares
about, not milliseconds on a small test set."

If the plan differs, use the terminal's actual result. Confirm the cluster and namespace, that
the build completed, and that Copilot did not change the query.

## 12:30 Follow the DBA's questions

Pick what they ask about.

Slow query log (depends on the connector exposing the log tool):

```text
Check the server's recent log for slow query entries on leafy_dba.work_items. Summarize the query shapes, durations and plan summaries you find. Does the log tell the same story as the profiler? Keep this read-only.
```

Alerts and Performance Advisor:

```text
In project <PROJECT_ID>, inspect triggered alerts and any available Performance Advisor recommendations for <CLUSTER_NAME>. Separate actual findings from unavailable data. If recommendations are empty, say so. Do not infer that the cluster is healthy or fabricate slow queries. Keep this read-only.
```

Access boundary:

```text
Explain the difference between my delegated Atlas access through this source and the database user's permissions used by a separate Python script. Separate facts you can inspect here from settings I must confirm in Atlas. Do not request or display credentials.
```

| Topic | Evidence to ask for | Limit to explain |
|---|---|---|
| Alerts | Triggered alerts in the selected project | No alerts returned is not proof of no problems |
| Performance Advisor | Actual recommendations | It reacts to slow queries over time; a short demo may produce none |
| Backups and recovery | Current policy, retention and recovery configuration in Atlas | The fixture says nothing about backup health; do not simulate a restore |
| Access | Signed-in identity, delegated roles and Read mode | Terminal database-user permissions differ from Copilot's Atlas identity |

## 14:30 Close

Say: "We found the environment, found two indexes to drop, read the profiler to find what was
slow, explained the worst query, fixed it and proved it does 1,500 times less work. Every step
showed its evidence."

For a five-minute version, run prompts 3, 4, 6 and 7, with the index change before prompt 7.
Add prompt 5 if there is time.

## Reset after the session

```bash
.venv/bin/python demos/leafy-dba/scripts/manage_index.py --undo
.venv/bin/python demos/leafy-dba/scripts/demo_queries.py --check --phase baseline
```

This removes only the index you created on stage. The planted indexes, usage counters and
profiler records stay, so you can present again the same day as is. If the cluster has
restarted, or the counters are from an earlier day, rerun the three commands under "Before the
audience arrives" first. No other demo needs to be reset.

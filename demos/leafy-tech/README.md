# Leafy Tech: the Willow Bend quote

A fictional IT reseller checks a $930,950 laptop quote against live Atlas data, Teams notes and
OneDrive documents. Built for technical audiences. The script is in `DEMO_SCRIPT.md`, the
prompts in `stage/prompts.txt`, and the setup talk in
[SETUP_ORIENTATION.md](../../SETUP_ORIENTATION.md).

## What is in this folder

| Path | What it is |
|---|---|
| `DEMO_SCRIPT.md` | The story, timing, what to say, expected answers |
| `stage/prompts.txt` | Prompts to paste into Copilot, plus fallbacks |
| `data/*.json` | The generated data, committed so you can load it straight away |
| `scripts/generate_data.py` | Rewrites `data/*.json`. Same output every run |
| `scripts/load_atlas.py` | Loads `data/*.json` into Atlas and builds the indexes |
| `scripts/demo_queries.py` | Runs every demo query directly on Atlas. `--check` exits 1 if a checked number drifted |
| `scripts/live_insert.py` | Lands a truck of laptops during the demo. `--undo` reverses it |
| `scripts/build_documents.py` | Builds the Word files and the Teams post sheet |
| `teams/TEAMS_MESSAGES.md` | Five Teams posts to make (subjects included) |
| `onedrive/` | Three Word files to upload to your work OneDrive |
| `fallback/` | A Word copy of the Teams posts, for when Teams is not indexed |

## Setup

Do the [shared setup](../../README.md#shared-setup) first. It creates the Python virtual
environment and the `.env` file that holds `MONGODB_URI`. Run every command below from the
project root.

The scripts use the database `leafy_tech`, on the same cluster as the other demos. To use
another name, set `MONGODB_DB_TECH` in `.env`. The stage prompts do not name the database. Only
the connection fallback names `leafy_tech`, so change it there too.

### 1. Teams (do this at least two days ahead)

Create the team **Leafy Tech (DEMO)** with a standard channel **Willow Bend Refresh**. Make the
five posts in `teams/TEAMS_MESSAGES.md`, with the subjects shown. Teams posts can take several
hours or more to become searchable by Copilot, so do this first.

### 2. Atlas

The data is already in `data/*.json`. Load it, which replaces the data in `leafy_tech` and builds
the indexes, including the vector index `product_semantic`:

```bash
.venv/bin/python demos/leafy-tech/scripts/load_atlas.py
```

Then check the numbers the demo depends on:

```bash
.venv/bin/python demos/leafy-tech/scripts/demo_queries.py --check
```

You only need `generate_data.py` if you change the data. It rewrites `data/*.json`, and gives the
same output every run:

```bash
.venv/bin/python demos/leafy-tech/scripts/generate_data.py
```

### 3. Connect Copilot to Atlas

Follow "Setup in five steps" in [SETUP_ORIENTATION.md](../../SETUP_ORIENTATION.md#setup-in-five-steps).

### 4. OneDrive

Upload the three files in `onedrive/` to your **work** OneDrive. If the Teams posts are not
searchable yet, also upload `fallback/Willow Bend Refresh channel export.docx`. It holds the same
posts.

### 5. Dry run

Open a new Copilot chat. In Copilot's model picker, choose a named model, not Auto. Auto did not
call the connector in our tests. This demo uses **Opus 5.5**, with **6.1 sol** as the backup.
Rehearse with the model you will present on. Run every prompt in `stage/prompts.txt` once, in
order, in one chat. Record your own dry run, so you have something to show if Copilot stalls on
stage.

Between Prompts 1a and 1b, run:

```bash
.venv/bin/python demos/leafy-tech/scripts/live_insert.py
```

`live_insert.py` writes to your cluster. It raises the MedBook 14 Clinical's Chicago stock from
150 to 330 and adds one receipt. Before you present, reverse it:

```bash
.venv/bin/python demos/leafy-tech/scripts/live_insert.py --undo
```

If you forget, Prompt 1a shows 500 available instead of 320, and `demo_queries.py --check` fails.

## Rebuild the documents

You only need this if you change the wording of the Word files or the Teams posts. It rebuilds
`onedrive/`, `fallback/` and `teams/TEAMS_MESSAGES.md`:

```bash
.venv/bin/python demos/leafy-tech/scripts/build_documents.py
```

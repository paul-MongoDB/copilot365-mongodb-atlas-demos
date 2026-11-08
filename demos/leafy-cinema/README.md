# Demo: Copilot + MongoDB Atlas, "Friday night at Leafy Cinema"

A 10-minute demo of Microsoft 365 Copilot reasoning over live Atlas data together with Teams
and OneDrive. The data is `sample_mflix`, the movie database that ships with Atlas, so there is
nothing to generate or load. Leafy Cinema is fictional.

Read `DEMO_SCRIPT.md` for the story, the beats and the expected answers.

## What is in this folder

| Path | What it is |
|---|---|
| `DEMO_SCRIPT.md` | The story, timing, what to say, expected answers |
| `stage/prompts.txt` | Prompts to paste into Copilot, plus Q&A prompts and fallbacks |
| `scripts/demo_queries.py` | Runs every demo query directly on Atlas. `--check` exits 1 if a number drifted |
| `scripts/live_insert.py` | Adds one fictional film during the demo. `--undo` removes it |
| `scripts/build_documents.py` | Builds the Word files and the Teams post sheet |
| `teams/TEAMS_MESSAGES.md` | Four Teams posts to make (subjects included) |
| `onedrive/` | Three Word files to upload to your work OneDrive |
| `fallback/` | A Word copy of the Teams posts, for when Teams is not indexed |

## Setup

Run these from the project root. The shared `.env` holds `MONGODB_URI`.

### 1. Atlas

`sample_mflix` must be loaded on the cluster (Atlas, "Load Sample Dataset"). The vector index
`vector_index_fullplot` on `embedded_movies.fullplot` (Automated Embedding, model `voyage-4`)
must exist and be queryable. Check both:

```bash
.venv/bin/python demos/leafy-cinema/scripts/demo_queries.py --check
```

Then connect the MongoDB Atlas source to Copilot, as in the insurance demo.

### 2. Teams (do this two days ahead)

Create the team **Leafy Cinema (DEMO)** with a channel **Hidden Gems**. Post the four
messages from `teams/TEAMS_MESSAGES.md`, using the subjects shown. Teams posts were not
searchable by Copilot several hours after posting in the insurance demo.

### 3. OneDrive

Upload the three files in `onedrive/` to your **work** OneDrive. If Teams isn't searchable yet,
also upload `fallback/Hidden Gems channel export.docx`.

### 4. Dry run

Open a new Copilot chat, set the model to **6.1 sol**, and run the prompts in order. Between
Prompts 1a and 1b, run:

```bash
.venv/bin/python demos/leafy-cinema/scripts/live_insert.py
```

Afterwards, remove the inserted film:

```bash
.venv/bin/python demos/leafy-cinema/scripts/live_insert.py --undo
```

## Rebuild the documents

```bash
.venv/bin/python demos/leafy-cinema/scripts/build_documents.py
```

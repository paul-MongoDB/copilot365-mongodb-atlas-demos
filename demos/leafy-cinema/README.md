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
| `scripts/demo_queries.py` | Runs every demo query directly on Atlas. `--check` checks the key numbers and exits 1 if one drifted |
| `scripts/live_insert.py` | Adds one fictional film during the demo. `--undo` removes it |
| `scripts/build_documents.py` | Builds the Word files and the Teams post sheet |
| `teams/TEAMS_MESSAGES.md` | Four Teams posts to make (subjects included) |
| `onedrive/` | Three Word files to upload to your work OneDrive |
| `fallback/` | A Word copy of the Teams posts, for when Teams is not indexed |

## Setup

Do the [shared setup](../../README.md#shared-setup) first. It creates the Python virtual
environment and the `.env` file that holds `MONGODB_URI`. Run every command below from the
project root.

The scripts use the database `sample_mflix`. To use another name, set `MONGODB_DB_MOVIES` in
`.env`. The stage prompts do not name the database. Only the connection fallback names
`sample_mflix`, so change it there too.

### 1. Teams (do this at least two days ahead)

Create the team **Leafy Cinema (DEMO)** with a channel **Hidden Gems**. Post the four
messages from `teams/TEAMS_MESSAGES.md`, using the subjects shown. Teams posts can take
several hours or more to become searchable by Copilot, so post them first.

### 2. Atlas: sample data and vector index

Load the sample data. In Atlas, open your cluster's **...** menu and choose **Load Sample
Dataset**. This creates `sample_mflix`.

Create the vector index. `sample_mflix` does not include it. In Atlas, open your cluster, go to
**Search & Vector Search**, and create a **Vector Search** index with the **JSON editor**. Choose
the database `sample_mflix` and the collection `embedded_movies`. Name the index
`vector_index_fullplot` and paste this definition:

```json
{
  "fields": [
    {"type": "autoEmbed", "modality": "text", "path": "fullplot", "model": "voyage-4"}
  ]
}
```

This uses Automated Embedding: Atlas embeds each film's `fullplot` with Voyage AI, and embeds
the query text at query time. You write no embedding code. Wait until the index shows as ready,
then check the data and the index:

```bash
.venv/bin/python demos/leafy-cinema/scripts/demo_queries.py --check
```

### 3. Connect Copilot to Atlas

Follow "Setup in five steps" in [SETUP_ORIENTATION.md](../../SETUP_ORIENTATION.md#setup-in-five-steps).

### 4. OneDrive

Upload the three files in `onedrive/` to your **work** OneDrive. If Teams isn't searchable yet,
also upload `fallback/Hidden Gems channel export.docx`.

### 5. Dry run

Open a new Copilot chat. In Copilot's model picker, choose a named model, not Auto. Auto did
not call the connector in our tests. We rehearsed this demo on **6.1 sol**. Rehearse with the
model you will present on, and run the prompts in order. Record your own dry run, so you have
something to show if Copilot stalls on stage.

Between Prompts 1a and 1b, run:

```bash
.venv/bin/python demos/leafy-cinema/scripts/live_insert.py
```

`live_insert.py` writes to your cluster. It adds one fictional film, "The Projectionist of
Marigold Falls", to both `movies` and `embedded_movies` in `sample_mflix`. Afterwards, remove
it from both:

```bash
.venv/bin/python demos/leafy-cinema/scripts/live_insert.py --undo
```

If you forget, Prompt 1a shows the film before the insert, and `demo_queries.py --check` fails.

## Rebuild the documents

You only need this if you change the wording of the Word files or the Teams posts. It rebuilds
`onedrive/`, `fallback/` and `teams/TEAMS_MESSAGES.md`:

```bash
.venv/bin/python demos/leafy-cinema/scripts/build_documents.py
```

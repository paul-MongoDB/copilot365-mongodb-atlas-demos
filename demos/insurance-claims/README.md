# Microsoft 365 Copilot + MongoDB Atlas demo: Contoso Mutual claims

This is a demo of Microsoft 365 Copilot answering an insurance claims question. It
combines three sources: claim records in MongoDB Atlas (through the federated connector),
policy documents in OneDrive, and team conversations in Teams. The story and the prompts
are in [DEMO_SCRIPT.md](DEMO_SCRIPT.md).

Everything here is fictional. Contoso Mutual, the people, the contractors, the claims and the
addresses are made up. Any resemblance to a real person, business or address is a coincidence.
No real business is accused of anything. See the [disclaimer](../../README.md#disclaimer).

## What is in this folder

| Path | What it is |
|---|---|
| `data/claims.json`, `data/policies.json` | 279 claims and 279 policies (MongoDB Extended JSON) |
| `onedrive/*.docx` | 4 Word documents to upload to OneDrive |
| `teams/TEAMS_MESSAGES.md` | 5 Teams posts to seed, with who posts each |
| `DEMO_SCRIPT.md` | The 10-minute run of show: prompts, expected answers, what to say |
| `stage/stopwatch.html` | Optional on-screen clock, with an opening screen (the old way in six steps) and a closing screen (old way vs today). Space advances, R resets |
| `stage/prompts.txt` | Every prompt for copy and paste, with no database names: Prompts 1 to 5 (Prompt 4 is two questions, 4a and 4b, around the live insert), the optional closer, the Q&A prompts and the fallbacks |
| `stage/prompts-explicit.txt` | The same prompts naming the Atlas project, cluster and database. Backup only |
| `fallback/*.docx` | The five Teams posts as a Word file. Upload it to OneDrive too, as a backup in case Teams is not indexed |
| `scripts/generate_data.py` | Rebuilds `data/` (fixed seed, so the answers stay the same) |
| `scripts/build_documents.py` | Rebuilds `onedrive/`, and rebuilds `fallback/` from `teams/TEAMS_MESSAGES.md`. Rerun it after editing the posts |
| `scripts/load_atlas.py` | Loads Atlas and creates the indexes, including the vector index |
| `scripts/demo_queries.py` | Read only. Runs the queries behind the prompts and prints the expected answers |
| `scripts/live_insert.py` | Adds one new LeafyDry claim during Prompt 4 (the live insert) to show Copilot reads Atlas live; `--undo` removes it |

## Setup (about 30 minutes, plus two days for Teams indexing)

Before you start, the MongoDB federated connector must be on in Microsoft 365 and Atlas
must allow AI clients. [Setup in five steps](../../SETUP_ORIENTATION.md#setup-in-five-steps)
covers both. Run every command below from the repo root.

### 1. Atlas

```bash
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
cp .env.example .env   # then put your connection string in .env
.venv/bin/python demos/insurance-claims/scripts/load_atlas.py
.venv/bin/python demos/insurance-claims/scripts/demo_queries.py --vector
```

This creates the `contoso_claims` database with `claims` and `policies` collections. It
also creates a vector search index named `claims_semantic` on `claims.loss_description`.

The vector index uses Atlas Automated Embedding (index field type `autoEmbed`, model
`voyage-4`). Atlas generates the embeddings itself, so the documents hold no vectors and no
embedding code runs here. `$vectorSearch` takes plain text in its `query` field. That
matters for Copilot, because the connector can pass the user's words straight through.

Two requirements to check on your cluster:
- Automated Embedding must be available on your cluster tier. On dedicated clusters (M10
  and up), Atlas also requires storage auto-scaling to be on.
- The federated connector must expose the `aggregate` tool, because `$vectorSearch` runs
  inside an aggregation.

`demo_queries.py --vector` settles the first one. If it prints a ranked list, the index
works. Prompts 2 and 3 in Copilot settle the second: Prompt 2 needs `aggregate` for a
`$group`, and Prompt 3 needs it for `$vectorSearch`.

### 2. OneDrive

Upload the four files in `onedrive/` to a folder such as `OneDrive/Contoso Claims Demo/`:

- Contoso Homeowners Policy Form HO-3 (2026).docx
- Contoso Endorsement HO-WB Water Backup.docx
- Contoso Property Claims Handling Guidelines (Rev 2026-07).docx
- Contoso Preferred Vendor Program - Q4 2026.docx

### 3. Teams

Follow [teams/TEAMS_MESSAGES.md](teams/TEAMS_MESSAGES.md). Teams posts can take several
hours or more to become searchable, so post at least two days ahead. Also upload
`fallback/DFW Property Claims channel export.docx` to the same OneDrive folder, as a backup
in case Teams is not indexed by demo day.

The story's team lead is Paul, the presenter. If you present under another name, replace
"Paul" in `teams/TEAMS_MESSAGES.md` (Post 2 and its reply), then rebuild the fallback:

```bash
.venv/bin/python demos/insurance-claims/scripts/build_documents.py
```

### 4. Dry run

Open one new Copilot chat. In Copilot's model picker, choose a named model, not Auto. Auto
did not call the connector in our tests. "6.1 sol" worked in rehearsal. Rehearse with the
model you will present on.

Run every prompt in `DEMO_SCRIPT.md` once, including the live insert, and compare the
answers with the expected answers there. Copilot's wording will vary between runs. The
numbers should not. Record your own dry run, so you have a backup if Copilot stalls on
stage.

When you finish, remove the live claim so the data is back to the scripted state:

```bash
.venv/bin/python demos/insurance-claims/scripts/live_insert.py --undo
```

## Regenerating

`generate_data.py` uses a fixed seed. Running it again produces identical data, so the
expected answers in `DEMO_SCRIPT.md` stay correct. If you change the generator, rerun
`demo_queries.py` and update the expected answers in the script.

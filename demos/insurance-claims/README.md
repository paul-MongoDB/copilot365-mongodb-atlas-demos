# Copilot 365 + MongoDB Atlas demo: Contoso Mutual claims

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
| `stage/stopwatch.html` | Optional on-screen clock. Space advances, R resets |
| `stage/prompts.txt` | The five natural-language prompts (no database names), for copy and paste |
| `stage/prompts-explicit.txt` | The same prompts naming the Atlas project and cluster. Backup only |
| `fallback/*.docx` | The five Teams posts as a Word file. Upload it to OneDrive only if Teams is not indexed |
| `scripts/generate_data.py` | Rebuilds `data/` (fixed seed, so the answers stay the same) |
| `scripts/build_documents.py` | Rebuilds `onedrive/` |
| `scripts/load_atlas.py` | Loads Atlas and creates the indexes, including the vector index |
| `scripts/demo_queries.py` | Runs every query the demo needs and prints the expected answers |
| `scripts/live_insert.py` | Adds one new LeafyDry claim during Act 4 to show Copilot reads Atlas live; `--undo` removes it |

## Setup (about 30 minutes, plus a day for Teams indexing)

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
works. Prompt 5 in Copilot settles the second.

### 2. OneDrive

Upload the four files in `onedrive/` to a folder such as `OneDrive/Contoso Claims Demo/`:

- Contoso Homeowners Policy Form HO-3 (2026).docx
- Contoso Endorsement HO-WB Water Backup.docx
- Contoso Property Claims Handling Guidelines (Rev 2026-07).docx
- Contoso Preferred Vendor Program - Q4 2026.docx

### 3. Teams

Follow [teams/TEAMS_MESSAGES.md](teams/TEAMS_MESSAGES.md). Post at least a day before the
demo so Copilot has indexed the messages. Teams was still not indexed several hours after
posting, so also upload `fallback/DFW Property Claims channel export.docx` to OneDrive.

### 4. Dry run

Open one new Copilot chat, set the model picker to 6.1 sol (not Auto), and run every prompt in `DEMO_SCRIPT.md` once and compare the answers with the expected
answers there. Copilot's wording will vary between runs. The numbers should not.

## Regenerating

`generate_data.py` uses a fixed seed. Running it again produces identical data, so the
expected answers in `DEMO_SCRIPT.md` stay correct. If you change the generator, rerun
`demo_queries.py` and update the expected answers in the script.

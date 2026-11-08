# Copilot + MongoDB Atlas demos

Demos of Microsoft 365 Copilot (with Work IQ) reading live data in MongoDB Atlas through the
Atlas federated connector, together with Teams and OneDrive.

| Demo | Story | Data | Folder |
|---|---|---|---|
| Insurance claims | A claims team lead checks a water damage claim and uncovers a contractor pattern | `contoso_claims`, generated and loaded by script | [demos/insurance-claims](demos/insurance-claims/README.md) |
| Leafy Cinema (movies) | A cinema programmer checks a film lineup and finds a customer's forgotten movie | `sample_mflix`, ships with Atlas | [demos/leafy-cinema](demos/leafy-cinema/README.md) |
| Leafy Tech (IT reseller) | A sales director checks a laptop quote for technical audiences | `leafy_tech`, generated and loaded by script | [demos/leafy-tech](demos/leafy-tech/README.md) |
| Leafy DBA (operations) | A DBA finds indexes to drop, reads the profiler for slow queries, and verifies an index fix | `leafy_dba`, generated and loaded by script | [demos/leafy-dba](demos/leafy-dba/README.md) |

For how Copilot connects to Atlas, see [SETUP_ORIENTATION.md](SETUP_ORIENTATION.md).

Each demo folder has `DEMO_SCRIPT.md`, `README.md`, `stage/` (prompts) and `scripts/`.
The business demos also have `teams/`, `onedrive/` and `fallback/`. The Leafy DBA demo runs directly
against Atlas and needs no Microsoft 365 content seeding.

## Shared setup

```bash
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
cp .env.example .env   # then put your connection string in .env
```

`common/_env.py` loads `.env` for every script, so you can run any script from the project root:

```bash
.venv/bin/python demos/leafy-cinema/scripts/demo_queries.py --check
.venv/bin/python demos/insurance-claims/scripts/demo_queries.py
.venv/bin/python demos/leafy-dba/scripts/load_atlas.py --preview
```

Use the MongoDB Atlas source and one new Copilot chat per run. Rehearse the selected model's
tool calls before presenting. The business demos also use Work IQ for Microsoft 365 content;
the Leafy DBA demo requires only Atlas. See each walkthrough for its rehearsal settings.

## Adding a demo

Copy a folder under `demos/`, change the data and prompts, and keep the same layout.

## Security

- Use a dedicated sandbox Atlas cluster. Never point these scripts at production data.
  `load_atlas.py` drops and reloads the `contoso_claims` and `leafy_tech` collections.
  `live_insert.py` writes a demo record, and `--undo` removes it.
  The Leafy DBA loader creates `leafy_dba.work_items`; `--reset` replaces only its owned fixture and
  indexes. Its presenter script creates or removes one named index in that collection. Its
  workload script turns the database profiler on for `leafy_dba` only, and off again when done.
- Keep your connection string in `.env`, which git ignores. Never commit it or paste it into a
  prompt, issue or pull request.
- Give the scripts a database user limited to the demo databases. Give Copilot users read-only
  Atlas access, as described in [SETUP_ORIENTATION.md](SETUP_ORIENTATION.md).
- Seed Teams and OneDrive in a demo team or folder, away from real business content. The
  documents and posts are fictional, and Copilot treats them as real once they are indexed.
- If a credential is ever exposed, rotate it in Atlas first, then clean up the repo.

## Disclaimer

This is sample code for demonstrations. It is provided as is, with no warranty, and it is not
an official MongoDB or Microsoft product. It is not supported by either company.

All people, companies, contractors, claims, policies, addresses, quotes and conversations are
fictional. Any resemblance to a real person, business or address is a coincidence, and no real
business is accused of anything. Contoso, Fabrikam, Wingtip, Litware, Proseware and Adatum are
Microsoft's sample names. The Leafy Cinema demo uses the film catalog from MongoDB's public
`sample_mflix` dataset, and its license rates and film series are made up.

The insurance rules, coverage amounts and approval limits are invented for the story. They are
not insurance, legal or financial advice. MongoDB, Atlas, Microsoft, Copilot, Teams and OneDrive
are trademarks of their respective owners.

## License

Licensed under the [Apache License 2.0](LICENSE).

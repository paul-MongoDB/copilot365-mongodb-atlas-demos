# Leafy Tech: the Willow Bend quote

A fictional IT reseller checks a $930,950 laptop quote against live Atlas data, Teams notes and
OneDrive documents. Built for technical audiences. The script is in `DEMO_SCRIPT.md`, the
prompts in `stage/prompts.txt`, and the setup talk in `../../SETUP_ORIENTATION.md`.

## Atlas

Database `leafy_tech` on the same cluster as the other demos. Run these from the project root:

```bash
.venv/bin/python demos/leafy-tech/scripts/generate_data.py      # writes data/*.json, same output every run
.venv/bin/python demos/leafy-tech/scripts/load_atlas.py         # replaces the data, builds the indexes
.venv/bin/python demos/leafy-tech/scripts/demo_queries.py --check
```

## Microsoft 365

1. Upload the three files in `onedrive/` to OneDrive.
2. Upload `fallback/Willow Bend Refresh channel export.docx` too. Teams posts took more than a few
   hours to become searchable, so with less than a day to go, Copilot needs this copy.
3. Create the team and post the messages in `teams/TEAMS_MESSAGES.md`.
4. Run every prompt in `stage/prompts.txt` once, in order, in one chat, on 6.1 sol.
5. Run `live_insert.py --undo` before you present.

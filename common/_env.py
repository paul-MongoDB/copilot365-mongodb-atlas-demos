"""Load KEY=VALUE lines from the project's top-level .env into os.environ.
Never overrides a value that is already set. Shared by every demo's scripts."""
import os
from pathlib import Path

_path = Path(__file__).resolve().parent.parent / ".env"
if _path.exists():
    for _line in _path.read_text().splitlines():
        _line = _line.strip()
        if _line and not _line.startswith("#") and "=" in _line:
            _key, _val = _line.split("=", 1)
            os.environ.setdefault(_key.strip(), _val.strip().strip('"').strip("'"))

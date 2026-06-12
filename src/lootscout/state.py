from __future__ import annotations
import json
from pathlib import Path


def load_seen(path: Path) -> set[int]:
    if not Path(path).exists():
        return set()
    data = json.loads(Path(path).read_text())
    return set(int(x) for x in data)


def save_seen(path: Path, ids: set[int]) -> None:
    Path(path).write_text(json.dumps(sorted(ids)))

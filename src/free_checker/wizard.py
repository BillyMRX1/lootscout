from __future__ import annotations
import os
import secrets
import string
from pathlib import Path
import tomli_w


def random_topic() -> str:
    alphabet = string.ascii_lowercase + string.digits
    suffix = "".join(secrets.choice(alphabet) for _ in range(8))
    return f"free-games-{suffix}"


def write_config(path: Path, cfg: dict) -> None:
    Path(path).write_text(tomli_w.dumps(cfg))


def write_env(path: Path, secrets_map: dict) -> None:
    lines = [f"{k}={v}" for k, v in secrets_map.items()]
    p = Path(path)
    p.write_text("\n".join(lines) + "\n")
    os.chmod(p, 0o600)

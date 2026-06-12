from __future__ import annotations
import logging
import sys
from pathlib import Path

CONFIG_PATH = Path("config.toml")
ENV_PATH = Path(".env")
SEEN_PATH = Path("seen.json")


def _load_env_file(path: Path) -> None:
    """Minimal .env loader into os.environ (no external dep)."""
    import os
    if not path.exists():
        return
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        os.environ.setdefault(k.strip(), v.strip())


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

    cmd = argv[0] if argv else "run"

    if cmd == "setup":
        from . import wizard
        wizard.run_setup(CONFIG_PATH, ENV_PATH)
        return 0

    if cmd == "run":
        from . import config, main as runner
        _load_env_file(ENV_PATH)
        try:
            cfg = config.load(CONFIG_PATH)
        except FileNotFoundError:
            print("No config.toml — run: uv run free-checker setup", file=sys.stderr)
            return 1
        try:
            runner.run(cfg, SEEN_PATH)
        except Exception:
            logging.exception("Run failed; seen.json left untouched.")
            return 1
        return 0

    print(f"Unknown command: {cmd}\nUsage: free-checker [setup|run]", file=sys.stderr)
    return 2

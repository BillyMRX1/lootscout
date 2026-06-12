from __future__ import annotations
import logging
import sys
from pathlib import Path

CONFIG_PATH = Path("config.toml")
ENV_PATH = Path(".env")
SEEN_PATH = Path("seen.json")
FEED_PATH = Path("public/feed.xml")


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
            print("No config.toml — run: uv run lootscout setup", file=sys.stderr)
            return 1
        try:
            runner.run(cfg, SEEN_PATH)
        except Exception:
            logging.exception("Run failed; seen.json left untouched.")
            return 1
        return 0

    if cmd == "status":
        import os
        from . import status
        _load_env_file(ENV_PATH)
        return status.run_status(CONFIG_PATH, ENV_PATH, SEEN_PATH, FEED_PATH,
                                 env=dict(os.environ))

    if cmd in ("remove", "uninstall"):
        from . import remove
        return remove.run_remove(
            config_path=CONFIG_PATH, env_path=ENV_PATH, seen_path=SEEN_PATH,
            feed_path=FEED_PATH, install_dir=Path.cwd())

    print(f"Unknown command: {cmd}\nUsage: lootscout [setup|run|status|remove]",
          file=sys.stderr)
    return 2

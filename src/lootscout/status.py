from __future__ import annotations
import datetime as _dt
from pathlib import Path

from . import config as config_mod
from . import state as state_mod
from .channels import REQUIRED_SECRETS


def _mask(value: str) -> str:
    """Show only the last 4 characters of a secret; never the whole thing."""
    tail = value[-4:] if len(value) >= 4 else ""
    return "••••" + tail


def _ago(ts: float) -> str:
    delta = _dt.datetime.now() - _dt.datetime.fromtimestamp(ts)
    secs = int(delta.total_seconds())
    if secs < 90:
        return "just now"
    if secs < 3600:
        return f"{secs // 60}m ago"
    if secs < 86400:
        return f"{secs // 3600}h ago"
    return f"{secs // 86400}d ago"


def _count_feed_items(text: str) -> int:
    return text.count("<item>")


def run_status(config_path: Path, env_path: Path, seen_path: Path,
               feed_path: Path, env: dict) -> int:
    """Print a read-only health dashboard. Returns an exit code:
    0 = healthy, 1 = no config, 2 = config present but a health problem.
    """
    print("🔭 LootScout status\n")

    # --- Config ---
    try:
        cfg = config_mod.load(config_path, env=env)
    except FileNotFoundError:
        print(f"Config ({config_path.name})          ✗ not found")
        print("\nNo config.toml — run: uv run lootscout setup")
        return 1

    print(f"Config ({config_path.name})          ✓ found")
    print(f"  Platforms                   {', '.join(cfg.platforms)}")
    print(f"  Giveaway types              {', '.join(cfg.types)}")
    print(f"  Enabled channels            {', '.join(cfg.enabled) or '(none)'}")

    # --- Secrets / health ---
    print()
    env_found = "✓ found" if Path(env_path).exists() else "✗ not found"
    print(f"Secrets ({env_path.name})                {env_found}")
    healthy = True
    for channel in cfg.enabled:
        for key in REQUIRED_SECRETS.get(channel, []):
            value = env.get(key)
            if value:
                print(f"  {key:<26}✓ set ({_mask(value)})")
            else:
                healthy = False
                print(f"  {key:<26}✗ missing   ← {channel} enabled but secret absent")

    # --- State ---
    print()
    seen_path = Path(seen_path)
    if seen_path.exists():
        count = len(state_mod.load_seen(seen_path))
        when = _ago(seen_path.stat().st_mtime)
        print(f"State ({seen_path.name})             ✓ {count} giveaways tracked")
        print(f"  Last updated                {when}")
    else:
        print(f"State ({seen_path.name})             – none yet (first run will seed it)")

    # --- Feed ---
    print()
    feed_path = Path(feed_path)
    if feed_path.exists():
        items = _count_feed_items(feed_path.read_text())
        print(f"Feed ({feed_path.name})              ✓ {items} entries")
        site_url = cfg.section("rss").get("site_url", "")
        if site_url:
            print(f"  site_url                    {site_url}")
    else:
        print(f"Feed ({feed_path.name})              – not written yet")

    return 0 if healthy else 2

from __future__ import annotations
import logging
from pathlib import Path
from .channels.base import Channel, Giveaway
from .channels import PUSH_CHANNELS, PULL_CHANNELS
from . import state

log = logging.getLogger("lootscout")


def run_pipeline(current: list[Giveaway], channels: list[Channel], seen_path: Path) -> None:
    current_ids = {g.id for g in current}

    # Pull channels always run with the full current feed.
    for ch in channels:
        if ch.name in PULL_CHANNELS:
            try:
                ch.write_full(current)
            except Exception:
                log.exception("RSS/pull channel '%s' failed (non-fatal)", ch.name)

    first_run = not Path(seen_path).exists()
    if first_run:
        push = [ch for ch in channels if ch.name in PUSH_CHANNELS]
        if not push:
            state.save_seen(seen_path, current_ids)
            log.info("First run: seeded %d giveaways silently (no push channels).",
                     len(current_ids))
            return
        # Send ONE consolidated digest of everything currently live, so the user
        # sees the backlog without a flood — then seed only if it was delivered.
        header = f"🔭 LootScout is live — {len(current)} games currently free to keep:"
        all_ok = True
        for ch in push:
            try:
                ch.notify_digest(current, header)
                log.info("First run: sent digest of %d giveaway(s) via %s.",
                         len(current), ch.name)
            except Exception:
                all_ok = False
                log.exception("First-run digest via '%s' failed.", ch.name)
        if all_ok:
            state.save_seen(seen_path, current_ids)
        else:
            log.warning("First-run digest failed; leaving seen.json unset to retry.")
        return

    seen = state.load_seen(seen_path)
    new_ids = current_ids - seen
    new_games = [g for g in current if g.id in new_ids]

    if not new_games:
        log.info("No new giveaways.")
        return

    all_push_ok = True
    for ch in channels:
        if ch.name in PUSH_CHANNELS:
            try:
                ch.notify_new(new_games)
                log.info("Pushed %d new game(s) via %s.", len(new_games), ch.name)
            except Exception:
                all_push_ok = False
                log.exception("Push channel '%s' failed.", ch.name)

    if all_push_ok:
        state.save_seen(seen_path, current_ids)
    else:
        log.warning("A push channel failed; leaving seen.json unchanged to retry.")


def run(cfg, seen_path: Path) -> None:
    """Full run: fetch feed, build channels, run pipeline."""
    from .channels import build_channels
    from . import feed
    channels = build_channels(cfg)
    current = feed.fetch(cfg.platforms, cfg.type)
    run_pipeline(current, channels, seen_path)

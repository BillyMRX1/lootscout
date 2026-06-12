from __future__ import annotations
import subprocess
from pathlib import Path
from typing import Callable

import questionary

from .wizard import POINTER, WIZARD_STYLE

CRON_MARKER = "lootscout"

TARGET_RUNTIME = "runtime"
TARGET_CRON = "cron"
TARGET_INSTALL = "install_dir"


def detect_targets(config_path, env_path, seen_path, feed_path,
                   install_dir, cron_lines) -> dict:
    """Inspect the filesystem/crontab and report only what actually exists."""
    runtime = [Path(p) for p in (config_path, env_path, seen_path, feed_path)
               if Path(p).exists()]
    return {
        "runtime": runtime,
        "cron": list(cron_lines),
        "install_dir": Path(install_dir),
    }


def filter_crontab(crontab_text: str) -> tuple[str, list[str]]:
    """Return (new crontab text without lootscout lines, removed lines)."""
    kept, removed = [], []
    for line in crontab_text.splitlines():
        (removed if CRON_MARKER in line else kept).append(line)
    new_text = "\n".join(kept)
    if new_text:
        new_text += "\n"
    return new_text, removed


def discover_cron_lines(crontab_text: str) -> list[str]:
    return [ln for ln in crontab_text.splitlines() if CRON_MARKER in ln]


def delete_paths(paths) -> list[tuple[Path, bool]]:
    """Unlink each path; return (path, was_removed). Absent paths skipped."""
    results = []
    for p in paths:
        p = Path(p)
        if p.exists():
            p.unlink()
            results.append((p, True))
        else:
            results.append((p, False))
    return results


# --- I/O wrappers (replaced with fakes in tests) -----------------------------

def read_crontab() -> str:
    try:
        out = subprocess.run(["crontab", "-l"], capture_output=True, text=True)
    except FileNotFoundError:
        return ""
    return out.stdout if out.returncode == 0 else ""


def write_crontab(text: str) -> None:
    subprocess.run(["crontab", "-"], input=text, text=True, check=True)


def _select_targets(targets: dict) -> list[str]:
    choices = []
    runtime = targets["runtime"]
    if runtime:
        names = ", ".join(p.name for p in runtime)
        choices.append(questionary.Choice(
            f"Runtime files ({names})", value=TARGET_RUNTIME))
    if targets["cron"]:
        n = len(targets["cron"])
        choices.append(questionary.Choice(
            f"Scheduled job ({n} crontab entr{'y' if n == 1 else 'ies'} found)",
            value=TARGET_CRON))
    choices.append(questionary.Choice(
        f"Entire install dir ({targets['install_dir']})", value=TARGET_INSTALL))
    return questionary.checkbox(
        "What should LootScout remove?",
        choices=choices, pointer=POINTER, style=WIZARD_STYLE).ask() or []


def _confirm_input(prompt: str) -> str:
    return questionary.text(prompt).ask() or ""


# --- Orchestration -----------------------------------------------------------

def run_remove(*, config_path, env_path, seen_path, feed_path, install_dir,
               select_fn: Callable[[dict], list[str]] = _select_targets,
               confirm_input_fn: Callable[[str], str] = _confirm_input,
               crontab_read: Callable[[], str] = read_crontab,
               crontab_write: Callable[[str], None] = write_crontab) -> int:
    install_dir = Path(install_dir)
    cron_lines = discover_cron_lines(crontab_read())
    targets = detect_targets(config_path, env_path, seen_path, feed_path,
                             install_dir, cron_lines)

    selection = select_fn(targets)
    if not selection:
        print("Nothing selected — aborted.")
        return 0

    # --- Preview ---
    print("\nThe following will be removed:")
    if TARGET_RUNTIME in selection:
        for p in targets["runtime"]:
            print(f"  {p}")
    if TARGET_CRON in selection:
        for line in targets["cron"]:
            print(f"  crontab line: {line}")
    if TARGET_INSTALL in selection:
        print(f"  (you will be given the command to delete {install_dir})")

    # --- Typed confirm ---
    if TARGET_INSTALL in selection:
        expected = install_dir.name
        prompt = f"Type the directory name '{expected}' to confirm:"
    else:
        expected = "yes"
        prompt = "Type 'yes' to proceed:"
    if confirm_input_fn(prompt).strip() != expected:
        print("Confirmation did not match — nothing was removed.")
        return 1

    # --- Execute: cron first (so nothing fires mid-teardown) ---
    if TARGET_CRON in selection:
        new_text, removed = filter_crontab(crontab_read())
        crontab_write(new_text)
        for line in removed:
            print(f"✓ removed crontab line: {line}")

    if TARGET_RUNTIME in selection:
        for path, removed in delete_paths(targets["runtime"]):
            print(f"✓ removed {path}" if removed else f"– skipped {path} (absent)")

    if TARGET_INSTALL in selection:
        print("\nFinal step — run this to remove the code:")
        print(f"    rm -rf {install_dir}")

    return 0

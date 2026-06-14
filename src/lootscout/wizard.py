from __future__ import annotations
import os
from pathlib import Path
import tomli_w
import requests
import questionary
import questionary.prompts.common as _q_common

# questionary hardcodes round ● / ○ checkbox glyphs as module globals (no
# per-call override exists in 2.x). Reassign them to square boxes for a cleaner
# toggle, and use a diamond cursor.
_q_common.INDICATOR_SELECTED = "■"
_q_common.INDICATOR_UNSELECTED = "□"
POINTER = "◆"

# Default questionary renders checked rows as a reverse-video highlight block
# behind the label in many terminals. Turn that off so the label stays plain
# text — the ■ / □ square is the only checked/unchecked indicator. Only the ◆
# pointer is tinted, to show cursor position.
WIZARD_STYLE = questionary.Style([
    ("qmark", "fg:#5fd700 bold"),
    ("question", "bold"),
    ("pointer", "fg:#5fd700 bold"),
    ("selected", "noreverse"),     # checked label: plain text, no highlight block
    ("highlighted", "noreverse"),  # cursor row: plain text, no highlight block
])


def write_config(path: Path, cfg: dict) -> None:
    Path(path).write_text(tomli_w.dumps(cfg))


def write_env(path: Path, secrets_map: dict) -> None:
    lines = [f"{k}={v}" for k, v in secrets_map.items()]
    p = Path(path)
    p.write_text("\n".join(lines) + "\n")
    os.chmod(p, 0o600)


def detect_chat_id(token: str) -> str | None:
    resp = requests.get(
        f"https://api.telegram.org/bot{token}/getUpdates", timeout=20)
    resp.raise_for_status()
    results = resp.json().get("result", [])
    for update in reversed(results):
        msg = update.get("message") or update.get("edited_message")
        if msg and "chat" in msg:
            return str(msg["chat"]["id"])
    return None


# Grouped so the wizard isn't 18 redundant rows. `pc` is GamerPower's umbrella —
# it already covers Steam/Epic/GOG/itch/DRM-free — so individual PC stores aren't
# listed separately.
PLATFORM_GROUPS = {
    "PC (Steam/Epic/GOG/itch/…)": ["pc"],
    "PlayStation": ["ps4", "ps5"],
    "Xbox": ["xbox-one", "xbox-series-xs"],
    "Nintendo Switch": ["switch"],
    "Android": ["android"],
    "iOS": ["ios"],
    "VR": ["vr"],
}
ALL_PLATFORMS = "🌐 All platforms"

# GamerPower's `type` filter values, with friendly labels.
TYPE_GROUPS = {
    "Free games": "game",
    "Free loot": "loot",
    "Beta access": "beta",
}
ALL_TYPES = "🌐 All types"


def _dedupe(items: list[str]) -> list[str]:
    seen: set[str] = set()
    return [x for x in items if not (x in seen or seen.add(x))]


def resolve_platforms(selected: list[str]) -> list[str]:
    """Map chosen platform labels (incl. the All sentinel) to API slugs."""
    labels = PLATFORM_GROUPS.keys() if ALL_PLATFORMS in selected else selected
    return _dedupe([slug for label in labels for slug in PLATFORM_GROUPS.get(label, [])])


def resolve_types(selected: list[str]) -> list[str]:
    """Map chosen giveaway-type labels (incl. the All sentinel) to API values."""
    labels = TYPE_GROUPS.keys() if ALL_TYPES in selected else selected
    return _dedupe([TYPE_GROUPS[label] for label in labels if label in TYPE_GROUPS])


def sample_giveaway():
    """A synthetic giveaway used for setup-time test notifications."""
    from .channels.base import Giveaway
    return Giveaway(
        id=0,
        title="Test Notification 🎮",
        worth="$0.00",
        image="",
        description="If you can see this, your channel is configured correctly.",
        url="https://www.gamerpower.com",
        end_date="N/A",
        platforms="PC",
    )


def send_tests(channels) -> list[tuple[str, bool, str]]:
    """Send a sample notification through each channel; never raises.

    Returns a list of (channel_name, ok, error_message) tuples.
    """
    from .channels import PULL_CHANNELS
    sample = sample_giveaway()
    results: list[tuple[str, bool, str]] = []
    for ch in channels:
        try:
            if ch.name in PULL_CHANNELS:
                ch.write_full([sample])
            else:
                ch.notify_new([sample])
            results.append((ch.name, True, ""))
        except Exception as exc:  # report, don't abort the wizard
            results.append((ch.name, False, str(exc)))
    return results


CRON_MARKER = "lootscout"


def cron_line(project_dir: Path, uv_path: str) -> str:
    """The exact crontab line to run LootScout every 6h, with absolute paths."""
    return (f"0 */6 * * * cd {project_dir} && {uv_path} run lootscout "
            f">> {project_dir}/lootscout.log 2>&1")


def install_cron(crontab_text: str, line: str) -> str:
    """Return crontab text with the LootScout schedule installed (idempotent).

    Any pre-existing lootscout line is dropped first, so re-running setup
    refreshes a stale schedule rather than stacking duplicates.
    """
    kept = [ln for ln in crontab_text.splitlines() if CRON_MARKER not in ln]
    kept.append(line)
    return "\n".join(kept) + "\n"


def cron_notice(crontab_text: str, project_dir: Path, uv_path: str) -> str:
    """Return a message about the cron schedule state.

    setup does NOT install cron itself, so this tells the user plainly whether a
    job exists and, if not, exactly how to add one.
    """
    if CRON_MARKER in crontab_text:
        return "✓ A LootScout cron job is already scheduled — automatic checks are on."
    line = cron_line(project_dir, uv_path)
    return (
        "⚠️  No cron job is installed — LootScout will NOT run automatically.\n"
        "    `setup` does not install cron for you. To schedule it (every 6h),\n"
        "    run `crontab -e` and add this line:\n\n"
        f"    {line}\n\n"
        "    Then verify with: uv run lootscout status"
    )


def run_setup(config_path, env_path) -> None:
    print("LootScout — Setup\n")

    chosen = questionary.checkbox(
        "Which platforms to watch? (or pick 'All')",
        choices=[
            questionary.Choice(ALL_PLATFORMS),
            *[questionary.Choice(label, checked=(label == "PC (Steam/Epic/GOG/itch/…)"))
              for label in PLATFORM_GROUPS],
        ],
        pointer=POINTER,
        style=WIZARD_STYLE,
    ).ask()
    platforms = resolve_platforms(chosen or [])

    chosen_types = questionary.checkbox(
        "Which kinds of giveaway? (or pick 'All')",
        choices=[
            questionary.Choice(ALL_TYPES),
            *[questionary.Choice(label, checked=(label == "Free games"))
              for label in TYPE_GROUPS],
        ],
        pointer=POINTER,
        style=WIZARD_STYLE,
    ).ask()
    types = resolve_types(chosen_types or []) or ["game"]

    channels = questionary.checkbox(
        "Pick notification channels:",
        choices=[
            questionary.Choice("Telegram — private bot DM (recommended)",
                               value="telegram", checked=True),
            questionary.Choice("Email — Gmail", value="email"),
            questionary.Choice("RSS — for feed readers", value="rss", checked=True),
        ],
        pointer=POINTER,
        style=WIZARD_STYLE,
    ).ask()

    cfg = {"platforms": platforms, "types": types, "enabled": channels}
    env: dict[str, str] = {"GMAIL_USER": "", "GMAIL_APP_PASSWORD": "",
                           "RECIPIENT_EMAIL": "", "TELEGRAM_BOT_TOKEN": ""}

    if "telegram" in channels:
        print("\nCreate a bot via @BotFather, then paste its token.")
        token = questionary.password("Telegram bot token?").ask()
        env["TELEGRAM_BOT_TOKEN"] = token
        questionary.text("Now MESSAGE your bot, then press Enter.").ask()
        chat_id = detect_chat_id(token) or questionary.text("chat_id (auto-detect failed)?").ask()
        cfg["telegram"] = {"chat_id": chat_id}
        print(f"  Detected chat_id: {chat_id}")

    if "email" in channels:
        print("\nUse a dedicated Gmail + 16-char App Password (not your real password):")
        env["GMAIL_USER"] = questionary.text("Gmail address?").ask()
        # Gmail shows app passwords as 4 space-separated groups, but login wants
        # them with the spaces removed.
        app_pw = questionary.password("Gmail app password?").ask()
        env["GMAIL_APP_PASSWORD"] = (app_pw or "").replace(" ", "")
        env["RECIPIENT_EMAIL"] = questionary.text("Send notifications to?").ask()

    if "rss" in channels:
        out = questionary.text("RSS output path?", default="public/feed.xml").ask()
        url = questionary.text("Public feed URL?", default="https://yourvps.example/feed.xml").ask()
        cfg["rss"] = {"output_path": out, "site_url": url}

    write_config(config_path, cfg)
    write_env(env_path, env)
    print(f"\n✔ Wrote {config_path}")
    print(f"✔ Wrote {env_path} (chmod 600)")

    if channels and questionary.confirm(
        "Send a test notification to each channel now?", default=True
    ).ask():
        from . import config as config_mod
        from .channels import build_channels
        cfg_obj = config_mod.load(config_path, env=env)
        for name, ok, err in send_tests(build_channels(cfg_obj)):
            print(f"  {'✔' if ok else '✗'} {name}" + (f" — {err}" if err else ""))

    print("\nTest run: uv run lootscout\n")
    import shutil
    from . import remove
    uv_path = shutil.which("uv") or "uv"
    project_dir = Path.cwd()
    line = cron_line(project_dir, uv_path)
    existing = remove.read_crontab()

    if CRON_MARKER in existing:
        print(cron_notice(existing, project_dir, uv_path))   # already scheduled ✓
    elif questionary.confirm(
        "Install the cron job now? (automatic check every 6h)", default=True
    ).ask():
        try:
            remove.write_crontab(install_cron(existing, line))
            print(f"✓ Installed cron job (every 6h):\n    {line}")
            print("  Verify with: uv run lootscout status")
        except Exception as exc:
            print(f"✗ Could not install cron automatically ({exc}).")
            print(cron_notice(existing, project_dir, uv_path))
    else:
        print(cron_notice(existing, project_dir, uv_path))   # manual ⚠️ instructions

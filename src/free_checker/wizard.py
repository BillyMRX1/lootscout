from __future__ import annotations
import os
import secrets
import string
from pathlib import Path
import tomli_w
import requests
import questionary
import qrcode


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


def print_qr(text: str) -> None:
    qr = qrcode.QRCode(border=1)
    qr.add_data(text)
    qr.make()
    qr.print_ascii(invert=True)


PLATFORM_CHOICES = {
    "PC (Steam/Epic/GOG/itch/…)": ["pc"],
    "Xbox": ["xbox-one", "xbox-series-xs"],
    "Switch": ["switch"],
}


def run_setup(config_path, env_path) -> None:
    print("Free Game Checker — Setup\n")

    chosen = questionary.checkbox(
        "Which platforms to watch?",
        choices=[questionary.Choice(label, checked=True) for label in PLATFORM_CHOICES],
    ).ask()
    platforms = [slug for label in chosen for slug in PLATFORM_CHOICES[label]]

    channels = questionary.checkbox(
        "Pick notification channels:",
        choices=[
            questionary.Choice("ntfy.sh — phone/desktop push, no account (easiest)",
                               value="ntfy", checked=True),
            questionary.Choice("Telegram — bot DM", value="telegram"),
            questionary.Choice("Email — Gmail", value="email"),
            questionary.Choice("RSS — for feed readers", value="rss", checked=True),
        ],
    ).ask()

    cfg = {"platforms": platforms, "type": "game", "enabled": channels}
    env: dict[str, str] = {"GMAIL_USER": "", "GMAIL_APP_PASSWORD": "",
                           "RECIPIENT_EMAIL": "", "TELEGRAM_BOT_TOKEN": "", "NTFY_TOKEN": ""}

    if "ntfy" in channels:
        default_topic = random_topic()
        topic = questionary.text("ntfy topic?", default=default_topic).ask()
        server = questionary.text("ntfy server?", default="https://ntfy.sh").ask()
        cfg["ntfy"] = {"topic": topic, "server": server}
        sub_url = f"{server.rstrip('/')}/{topic}"
        print(f"\nSubscribe on your phone — open {sub_url} or scan:")
        print_qr(sub_url)
        token = questionary.password("ntfy auth token? (blank if public)").ask()
        env["NTFY_TOKEN"] = token or ""

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
        env["GMAIL_APP_PASSWORD"] = questionary.password("Gmail app password?").ask()
        env["RECIPIENT_EMAIL"] = questionary.text("Send notifications to?").ask()

    if "rss" in channels:
        out = questionary.text("RSS output path?", default="public/feed.xml").ask()
        url = questionary.text("Public feed URL?", default="https://yourvps.example/feed.xml").ask()
        cfg["rss"] = {"output_path": out, "site_url": url}

    write_config(config_path, cfg)
    write_env(env_path, env)
    print(f"\n✔ Wrote {config_path}")
    print(f"✔ Wrote {env_path} (chmod 600)")
    print("\nTest run: uv run free-checker")
    print("Cron (every 6h):")
    print("  0 */6 * * * cd $(pwd) && uv run free-checker >> checker.log 2>&1")

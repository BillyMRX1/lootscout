"""Channel registry and factory."""
from __future__ import annotations
from .base import Channel, Giveaway
from .email import EmailChannel
from .ntfy import NtfyChannel
from .telegram import TelegramChannel
from .rss import RssChannel

PUSH_CHANNELS = {"email", "ntfy", "telegram"}
PULL_CHANNELS = {"rss"}


def build_channels(cfg) -> list[Channel]:
    """Instantiate enabled channels from a Config; fails fast on missing secrets."""
    built: list[Channel] = []
    for name in cfg.enabled:
        if name == "ntfy":
            s = cfg.section("ntfy")
            built.append(NtfyChannel(
                topic=s["topic"], server=s.get("server", "https://ntfy.sh"),
                token=cfg.env.get("NTFY_TOKEN") or None))
        elif name == "telegram":
            built.append(TelegramChannel(
                token=cfg.require_secret("TELEGRAM_BOT_TOKEN"),
                chat_id=cfg.section("telegram")["chat_id"]))
        elif name == "email":
            built.append(EmailChannel(
                user=cfg.require_secret("GMAIL_USER"),
                password=cfg.require_secret("GMAIL_APP_PASSWORD"),
                recipient=cfg.require_secret("RECIPIENT_EMAIL")))
        elif name == "rss":
            s = cfg.section("rss")
            built.append(RssChannel(
                output_path=s.get("output_path", "public/feed.xml"),
                site_url=s.get("site_url", "")))
    return built

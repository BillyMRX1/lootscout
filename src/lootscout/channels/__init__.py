"""Channel registry and factory."""
from __future__ import annotations
from .base import Channel, Giveaway
from .email import EmailChannel
from .telegram import TelegramChannel
from .rss import RssChannel

PUSH_CHANNELS = {"email", "telegram"}
PULL_CHANNELS = {"rss"}

# Single source of truth for which .env secrets each channel needs. Kept in sync
# with the require_secret(...) calls in build_channels below (guarded by a test).
# Telegram's chat_id lives in config.toml, not .env, so it is not listed here.
REQUIRED_SECRETS = {
    "telegram": ["TELEGRAM_BOT_TOKEN"],
    "email": ["GMAIL_USER", "GMAIL_APP_PASSWORD", "RECIPIENT_EMAIL"],
    "rss": [],
}


def build_channels(cfg) -> list[Channel]:
    """Instantiate enabled channels from a Config; fails fast on missing secrets."""
    built: list[Channel] = []
    for name in cfg.enabled:
        if name == "telegram":
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

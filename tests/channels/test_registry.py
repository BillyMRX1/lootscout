import pytest
from lootscout import config
from lootscout.channels import build_channels

BASE = """
platforms = ["pc"]
type = "game"
enabled = ["telegram", "rss"]
[telegram]
chat_id = "123"
[rss]
output_path = "public/feed.xml"
site_url = "https://x/feed.xml"
"""

def test_build_channels_instantiates_enabled(tmp_path):
    p = tmp_path / "config.toml"; p.write_text(BASE)
    chans = build_channels(config.load(p, env={"TELEGRAM_BOT_TOKEN": "tok"}))
    assert {c.name for c in chans} == {"telegram", "rss"}

def test_build_channels_fails_fast_on_missing_telegram_secret(tmp_path):
    # telegram enabled but TELEGRAM_BOT_TOKEN absent in env
    p = tmp_path / "config.toml"; p.write_text(BASE)
    with pytest.raises(config.ConfigError):
        build_channels(config.load(p, env={}))

def test_build_channels_fails_fast_on_missing_email_secret(tmp_path):
    p = tmp_path / "config.toml"
    p.write_text(BASE.replace('["telegram", "rss"]', '["email"]'))
    with pytest.raises(config.ConfigError):
        build_channels(config.load(p, env={}))

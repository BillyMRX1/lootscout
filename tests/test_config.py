import os
import pytest
from lootscout import config

TOML = """
platforms = ["pc", "switch"]
type = "game"
enabled = ["telegram", "email"]

[telegram]
chat_id = "987654"
"""

def write(tmp_path, text=TOML):
    p = tmp_path / "config.toml"; p.write_text(text); return p

def test_load_parses_platforms_and_enabled(tmp_path):
    cfg = config.load(write(tmp_path), env={})
    assert cfg.platforms == ["pc", "switch"]
    assert cfg.types == ["game"]            # back-compat: old `type` string → list
    assert cfg.enabled == ["telegram", "email"]
    assert cfg.section("telegram")["chat_id"] == "987654"

def test_load_reads_types_list(tmp_path):
    toml = TOML.replace('type = "game"', 'types = ["game", "loot", "beta"]')
    cfg = config.load(write(tmp_path, toml), env={})
    assert cfg.types == ["game", "loot", "beta"]

def test_load_back_compat_period_joined_type(tmp_path):
    toml = TOML.replace('type = "game"', 'type = "game.loot"')
    cfg = config.load(write(tmp_path, toml), env={})
    assert cfg.types == ["game", "loot"]

def test_load_defaults_types_to_game(tmp_path):
    toml = TOML.replace('type = "game"', '')
    cfg = config.load(write(tmp_path, toml), env={})
    assert cfg.types == ["game"]

def test_enabled_channel_missing_secret_fails_fast(tmp_path):
    # email enabled but GMAIL_USER absent in env
    with pytest.raises(config.ConfigError) as e:
        config.load(write(tmp_path), env={}).require_secret("GMAIL_USER")
    assert "GMAIL_USER" in str(e.value)

def test_require_secret_returns_value_when_present(tmp_path):
    cfg = config.load(write(tmp_path), env={"GMAIL_USER": "a@b.com"})
    assert cfg.require_secret("GMAIL_USER") == "a@b.com"

def test_unknown_enabled_channel_rejected(tmp_path):
    bad = TOML.replace('["telegram", "email"]', '["bogus"]')
    with pytest.raises(config.ConfigError):
        config.load(write(tmp_path, bad), env={})

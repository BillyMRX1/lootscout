import tomllib, stat, os
from pathlib import Path
from free_checker import wizard

def test_write_config_produces_loadable_toml(tmp_path):
    cfg = {
        "platforms": ["pc", "switch"], "type": "game",
        "enabled": ["ntfy", "rss"],
        "ntfy": {"topic": "free-x", "server": "https://ntfy.sh"},
        "rss": {"output_path": "public/feed.xml", "site_url": "https://x/feed.xml"},
    }
    p = tmp_path / "config.toml"
    wizard.write_config(p, cfg)
    loaded = tomllib.loads(p.read_text())
    assert loaded["enabled"] == ["ntfy", "rss"]
    assert loaded["ntfy"]["topic"] == "free-x"

def test_write_env_sets_chmod_600(tmp_path):
    p = tmp_path / ".env"
    wizard.write_env(p, {"GMAIL_USER": "a@b.com", "NTFY_TOKEN": ""})
    text = p.read_text()
    assert "GMAIL_USER=a@b.com" in text
    mode = stat.S_IMODE(os.stat(p).st_mode)
    assert mode == 0o600

def test_random_topic_is_obscure():
    t = wizard.random_topic()
    assert t.startswith("free-games-")
    assert len(t) > len("free-games-") + 6

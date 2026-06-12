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

def test_sample_giveaway_is_a_giveaway():
    from free_checker.channels.base import Giveaway
    s = wizard.sample_giveaway()
    assert isinstance(s, Giveaway)
    assert s.title  # has a recognizable test title

class _FakePush:
    name = "ntfy"
    def __init__(self, fail=False): self.fail = fail; self.got = None
    def notify_new(self, games):
        if self.fail: raise RuntimeError("boom")
        self.got = games
    def write_full(self, games): pass

class _FakePull:
    name = "rss"
    def __init__(self): self.got = None
    def notify_new(self, games): pass
    def write_full(self, games): self.got = games

def test_send_tests_routes_push_and_pull_and_reports():
    push, pull, broken = _FakePush(), _FakePull(), _FakePush(fail=True)
    broken.name = "telegram"
    results = wizard.send_tests([push, pull, broken])
    by_name = {name: (ok, err) for name, ok, err in results}
    assert by_name["ntfy"][0] is True       # push got the sample
    assert by_name["rss"][0] is True         # pull.write_full called
    assert by_name["telegram"][0] is False   # failure captured, not raised
    assert push.got and pull.got            # both received the sample giveaway

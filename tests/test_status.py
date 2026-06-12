from lootscout import status

CONFIG = """
platforms = ["pc", "switch"]
type = "game"
enabled = ["telegram", "rss"]

[telegram]
chat_id = "987654"

[rss]
output_path = "public/feed.xml"
site_url = "https://example.com/feed.xml"
"""

FEED = """<?xml version='1.0' encoding='utf-8'?>
<rss version="2.0"><channel>
<item><title>A</title></item>
<item><title>B</title></item>
</channel></rss>"""


def _paths(tmp_path):
    return {
        "config_path": tmp_path / "config.toml",
        "env_path": tmp_path / ".env",
        "seen_path": tmp_path / "seen.json",
        "feed_path": tmp_path / "feed.xml",
    }


def test_missing_config_returns_1_with_setup_hint(tmp_path, capsys):
    p = _paths(tmp_path)
    rc = status.run_status(**p, env={})
    out = capsys.readouterr().out
    assert rc == 1
    assert "setup" in out.lower()


def test_healthy_config_returns_0_and_summarizes(tmp_path, capsys):
    p = _paths(tmp_path)
    p["config_path"].write_text(CONFIG)
    p["env_path"].write_text("TELEGRAM_BOT_TOKEN=abc1234\n")
    rc = status.run_status(**p, env={"TELEGRAM_BOT_TOKEN": "abc1234"})
    out = capsys.readouterr().out
    assert rc == 0
    assert "pc" in out and "switch" in out      # platforms
    assert "telegram" in out and "rss" in out    # enabled channels


def test_masks_secret_value_and_never_leaks_it(tmp_path, capsys):
    p = _paths(tmp_path)
    p["config_path"].write_text(CONFIG)
    secret = "SUPERSECRETTOKEN9999"
    p["env_path"].write_text(f"TELEGRAM_BOT_TOKEN={secret}\n")
    status.run_status(**p, env={"TELEGRAM_BOT_TOKEN": secret})
    out = capsys.readouterr().out
    assert secret not in out                     # full value never printed
    assert "••••" in out or "*" in out           # some masking shown


def test_missing_secret_for_enabled_channel_returns_2(tmp_path, capsys):
    p = _paths(tmp_path)
    cfg = CONFIG.replace('["telegram", "rss"]', '["telegram", "email"]')
    p["config_path"].write_text(cfg)
    # telegram token present, but email secrets absent
    rc = status.run_status(**p, env={"TELEGRAM_BOT_TOKEN": "abc1234"})
    out = capsys.readouterr().out
    assert rc == 2
    assert "GMAIL_APP_PASSWORD" in out
    assert "missing" in out.lower()


def test_reports_state_count_and_feed_count(tmp_path, capsys):
    p = _paths(tmp_path)
    p["config_path"].write_text(CONFIG)
    p["env_path"].write_text("TELEGRAM_BOT_TOKEN=abc1234\n")
    p["seen_path"].write_text("[10, 20, 30]")
    p["feed_path"].write_text(FEED)
    status.run_status(**p, env={"TELEGRAM_BOT_TOKEN": "abc1234"})
    out = capsys.readouterr().out
    assert "3" in out                            # 3 giveaways tracked
    assert "2" in out                            # 2 feed entries

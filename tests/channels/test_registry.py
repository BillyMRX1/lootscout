import pytest
from lootscout import config
from lootscout.channels import build_channels

BASE = """
platforms = ["pc"]
type = "game"
enabled = ["ntfy", "rss"]
[ntfy]
topic = "t"
server = "https://ntfy.sh"
[rss]
output_path = "public/feed.xml"
site_url = "https://x/feed.xml"
"""

def test_build_channels_instantiates_enabled(tmp_path):
    p = tmp_path / "config.toml"; p.write_text(BASE)
    chans = build_channels(config.load(p, env={}))
    assert {c.name for c in chans} == {"ntfy", "rss"}

def test_build_channels_fails_fast_on_missing_email_secret(tmp_path):
    p = tmp_path / "config.toml"
    p.write_text(BASE.replace('["ntfy", "rss"]', '["email"]'))
    with pytest.raises(config.ConfigError):
        build_channels(config.load(p, env={}))

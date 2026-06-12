import inspect
import re
from lootscout import channels
from lootscout.config import VALID_CHANNELS


def test_required_secrets_covers_every_channel():
    # Every valid channel must have an entry (even if it needs no secrets).
    assert set(channels.REQUIRED_SECRETS) == VALID_CHANNELS


def test_required_secrets_matches_build_channels_calls():
    # Drift guard: every require_secret("X") literal in build_channels must be
    # declared in REQUIRED_SECRETS, so the two never fall out of sync.
    src = inspect.getsource(channels.build_channels)
    referenced = set(re.findall(r'require_secret\(["\']([^"\']+)["\']\)', src))
    declared = {key for keys in channels.REQUIRED_SECRETS.values() for key in keys}
    assert referenced == declared


def test_rss_requires_no_secrets():
    assert channels.REQUIRED_SECRETS["rss"] == []

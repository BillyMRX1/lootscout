from unittest.mock import MagicMock
from lootscout import main
from lootscout.channels.base import Giveaway

def g(i): return Giveaway(i, f"G{i}", "$9", "", "d", "u", "N/A", "PC")

class FakePush:
    name = "telegram"
    def __init__(self, fail=False): self.fail = fail; self.notified = None
    def notify_new(self, games):
        if self.fail: raise RuntimeError("boom")
        self.notified = games
    def write_full(self, games): pass

class FakePull:
    name = "rss"
    def __init__(self): self.full = None
    def notify_new(self, games): pass
    def write_full(self, games): self.full = games

def test_first_run_seeds_silently(tmp_path):
    push, pull = FakePush(), FakePull()
    seen = tmp_path / "seen.json"
    main.run_pipeline(current=[g(1), g(2)], channels=[push, pull], seen_path=seen)
    assert push.notified is None          # no push on first run
    assert {x.id for x in pull.full} == {1, 2}  # rss still gets full feed
    assert seen.exists()                  # state seeded

def test_new_games_notify_and_save(tmp_path):
    seen = tmp_path / "seen.json"
    import json; seen.write_text(json.dumps([1]))
    push, pull = FakePush(), FakePull()
    main.run_pipeline(current=[g(1), g(2)], channels=[push, pull], seen_path=seen)
    assert {x.id for x in push.notified} == {2}   # only new id 2
    assert json.loads(seen.read_text()) == [1, 2]

def test_no_new_games_skips_push(tmp_path):
    seen = tmp_path / "seen.json"
    import json; seen.write_text(json.dumps([1, 2]))
    push, pull = FakePush(), FakePull()
    main.run_pipeline(current=[g(1), g(2)], channels=[push, pull], seen_path=seen)
    assert push.notified is None
    assert pull.full is not None          # rss still rewritten

def test_push_failure_leaves_state_unchanged(tmp_path):
    seen = tmp_path / "seen.json"
    import json; seen.write_text(json.dumps([1]))
    push, pull = FakePush(fail=True), FakePull()
    main.run_pipeline(current=[g(1), g(2)], channels=[push, pull], seen_path=seen)
    assert json.loads(seen.read_text()) == [1]   # NOT updated — retry next run

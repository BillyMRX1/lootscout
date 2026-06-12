from pathlib import Path
from lootscout import state

def test_load_missing_file_returns_empty_set(tmp_path):
    assert state.load_seen(tmp_path / "seen.json") == set()

def test_save_then_load_round_trip(tmp_path):
    p = tmp_path / "seen.json"
    state.save_seen(p, {1, 2, 3})
    assert state.load_seen(p) == {1, 2, 3}

def test_save_overwrites_with_current_ids(tmp_path):
    p = tmp_path / "seen.json"
    state.save_seen(p, {1, 2, 3})
    state.save_seen(p, {2, 3, 4})   # expired id 1 drops out
    assert state.load_seen(p) == {2, 3, 4}

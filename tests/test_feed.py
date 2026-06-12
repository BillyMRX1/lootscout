import json
from pathlib import Path
from unittest.mock import patch, MagicMock
from free_checker import feed
from free_checker.channels.base import Giveaway

SAMPLE = json.loads((Path(__file__).parent / "sample_feed.json").read_text())

def test_parse_returns_giveaways():
    games = feed.parse(SAMPLE)
    assert len(games) == 2
    assert all(isinstance(g, Giveaway) for g in games)
    assert games[0].id == 3684

def test_parse_handles_na_end_date():
    games = feed.parse(SAMPLE)
    assert games[1].end_date == "N/A"

def test_build_url_includes_all_platforms_and_type():
    url = feed.build_url(["pc", "xbox-one", "switch"], "game")
    assert "platform=pc.xbox-one.switch" in url
    assert "type=game" in url

@patch("free_checker.feed.requests.get")
def test_fetch_calls_api_and_parses(mock_get):
    resp = MagicMock(); resp.json.return_value = SAMPLE; resp.raise_for_status = MagicMock()
    mock_get.return_value = resp
    games = feed.fetch(["pc"], "game")
    assert len(games) == 2
    mock_get.assert_called_once()

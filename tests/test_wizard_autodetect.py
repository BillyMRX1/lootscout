from unittest.mock import patch, MagicMock
from free_checker import wizard

@patch("free_checker.wizard.requests.get")
def test_detect_chat_id_reads_latest_update(mock_get):
    mock_get.return_value = MagicMock(
        raise_for_status=MagicMock(),
        json=lambda: {"ok": True, "result": [
            {"message": {"chat": {"id": 987654}, "text": "hi"}}]})
    assert wizard.detect_chat_id("123:abc") == "987654"

@patch("free_checker.wizard.requests.get")
def test_detect_chat_id_returns_none_when_no_updates(mock_get):
    mock_get.return_value = MagicMock(
        raise_for_status=MagicMock(), json=lambda: {"ok": True, "result": []})
    assert wizard.detect_chat_id("123:abc") is None

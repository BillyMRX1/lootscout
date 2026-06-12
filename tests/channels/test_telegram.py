from unittest.mock import patch, MagicMock
from free_checker.channels.telegram import TelegramChannel
from free_checker.channels.base import Giveaway

def g(i, t): return Giveaway(i, t, "$9", "", "d", "https://u", "N/A", "PC")

@patch("free_checker.channels.telegram.requests.post")
def test_notify_new_sends_message_to_chat(mock_post):
    mock_post.return_value = MagicMock(raise_for_status=MagicMock())
    ch = TelegramChannel(token="123:abc", chat_id="555")
    ch.notify_new([g(1, "Eets")])
    url = mock_post.call_args.args[0]
    assert url == "https://api.telegram.org/bot123:abc/sendMessage"
    payload = mock_post.call_args.kwargs["json"]
    assert payload["chat_id"] == "555"
    assert "Eets" in payload["text"]

@patch("free_checker.channels.telegram.requests.post")
def test_notify_new_skips_when_empty(mock_post):
    TelegramChannel("123:abc", "555").notify_new([])
    mock_post.assert_not_called()

@patch("free_checker.channels.telegram.requests.post")
def test_notify_new_escapes_html_in_title(mock_post):
    mock_post.return_value = MagicMock(raise_for_status=MagicMock())
    bad = Giveaway(1, "Command & Conquer <Tiberian>", "$9", "", "d", "https://u", "N/A", "PC")
    TelegramChannel("123:abc", "555").notify_new([bad])
    text = mock_post.call_args.kwargs["json"]["text"]
    assert "Command &amp; Conquer &lt;Tiberian&gt;" in text
    assert "Command & Conquer <Tiberian>" not in text

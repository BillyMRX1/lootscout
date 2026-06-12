from unittest.mock import patch, MagicMock
from free_checker.channels.ntfy import NtfyChannel
from free_checker.channels.base import Giveaway

def g(i, title): return Giveaway(i, title, "$9", "", "d", "https://u", "N/A", "PC")

@patch("free_checker.channels.ntfy.requests.post")
def test_notify_new_posts_one_message_per_game(mock_post):
    mock_post.return_value = MagicMock(raise_for_status=MagicMock())
    ch = NtfyChannel(topic="free-x", server="https://ntfy.sh", token=None)
    ch.notify_new([g(1, "Eets"), g(2, "Foo")])
    assert mock_post.call_count == 2
    # JSON publishing: POST to the server root with topic in the JSON body
    url = mock_post.call_args_list[0].args[0]
    assert url == "https://ntfy.sh"
    payload = mock_post.call_args_list[0].kwargs["json"]
    assert payload["topic"] == "free-x"
    assert "Eets" in payload["title"]
    assert payload["click"] == "https://u"

@patch("free_checker.channels.ntfy.requests.post")
def test_notify_new_skips_when_empty(mock_post):
    NtfyChannel("free-x", "https://ntfy.sh", None).notify_new([])
    mock_post.assert_not_called()

@patch("free_checker.channels.ntfy.requests.post")
def test_auth_token_sets_bearer_header(mock_post):
    mock_post.return_value = MagicMock(raise_for_status=MagicMock())
    NtfyChannel("free-x", "https://ntfy.sh", "tok").notify_new([g(1, "Eets")])
    headers = mock_post.call_args.kwargs["headers"]
    assert headers["Authorization"] == "Bearer tok"

@patch("free_checker.channels.ntfy.requests.post")
def test_unicode_title_stays_out_of_http_headers(mock_post):
    """Regression: emoji/CJK titles must not break latin-1 HTTP header encoding.

    ntfy publishes title/message in the JSON body (UTF-8), never in headers,
    so every header value must be latin-1 encodable.
    """
    mock_post.return_value = MagicMock(raise_for_status=MagicMock())
    ch = NtfyChannel("free-x", "https://ntfy.sh", "tok")
    ch.notify_new([g(1, "🎮 ガンダム & Co")])
    headers = mock_post.call_args.kwargs.get("headers", {})
    for value in headers.values():
        value.encode("latin-1")  # must not raise UnicodeEncodeError
    # The unicode title is carried in the JSON body instead.
    assert "ガンダム" in mock_post.call_args.kwargs["json"]["title"]

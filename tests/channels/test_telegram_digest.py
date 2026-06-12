from unittest.mock import patch, MagicMock
from lootscout.channels import telegram
from lootscout.channels.telegram import TelegramChannel, build_digest
from lootscout.channels.base import Giveaway


def g(i, title, url="https://u", worth="$9.99"):
    return Giveaway(i, title, worth, "", "d", url, "N/A", "PC")


def test_build_digest_has_header_and_hyperlinked_titles():
    msg = build_digest([g(1, "Eets", "https://x/eets")], header="LootScout is live:")
    assert "LootScout is live:" in msg
    # title is a clickable HTML link to the giveaway url
    assert '<a href="https://x/eets">Eets</a>' in msg
    assert "$9.99" in msg


def test_build_digest_escapes_html_in_title():
    msg = build_digest([g(1, "A & B <x>")], header="H")
    assert "A &amp; B &lt;x&gt;" in msg
    assert "A & B <x>" not in msg


def test_build_digest_truncates_when_too_long():
    many = [g(i, f"Game number {i} with a reasonably long title", f"https://x/{i}")
            for i in range(200)]
    msg = build_digest(many, header="H", limit=3900)
    assert len(msg) <= 3900
    assert "more" in msg.lower()            # shows an "…and N more" tail


@patch("lootscout.channels.telegram.requests.post")
def test_notify_digest_sends_one_message_no_preview(mock_post):
    mock_post.return_value = MagicMock(raise_for_status=MagicMock())
    ch = TelegramChannel(token="123:abc", chat_id="555")
    ch.notify_digest([g(1, "Eets"), g(2, "Foo")], header="Live:")
    assert mock_post.call_count == 1        # ONE consolidated message
    payload = mock_post.call_args.kwargs["json"]
    assert payload["chat_id"] == "555"
    assert payload["parse_mode"] == "HTML"
    assert payload["disable_web_page_preview"] is True
    assert "Eets" in payload["text"] and "Foo" in payload["text"]

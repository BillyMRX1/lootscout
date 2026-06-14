from unittest.mock import patch, MagicMock
from lootscout.channels import telegram
from lootscout.channels.telegram import TelegramChannel, build_digests
from lootscout.channels.base import Giveaway


def g(i, title, url="https://u", worth="$9.99"):
    return Giveaway(i, title, worth, "", "d", url, "N/A", "PC")


def test_build_digests_single_message_has_header_and_links():
    msgs = build_digests([g(1, "Eets", "https://x/eets")], header="LootScout is live:")
    assert len(msgs) == 1
    assert "LootScout is live:" in msgs[0]
    assert '<a href="https://x/eets">Eets</a>' in msgs[0]
    assert "$9.99" in msgs[0]


def test_build_digests_escapes_html_in_title():
    msgs = build_digests([g(1, "A & B <x>")], header="H")
    assert "A &amp; B &lt;x&gt;" in msgs[0]
    assert "A & B <x>" not in msgs[0]


def test_build_digests_splits_without_dropping_any_game():
    many = [g(i, f"Game number {i} with a reasonably long title", f"https://x/{i}")
            for i in range(200)]
    msgs = build_digests(many, header="H", limit=3900)
    assert len(msgs) > 1                         # must split, not truncate
    for m in msgs:
        assert len(m) <= 3900                    # every chunk under the cap
    # EVERY game appears across the messages — nothing dropped
    joined = "\n".join(msgs)
    game_lines = sum(line.startswith("🎮") for line in joined.splitlines())
    assert game_lines == 200
    assert "more" not in joined.lower()          # never a truncation tail


def test_build_digests_labels_parts_when_split():
    many = [g(i, f"Game number {i} with a reasonably long title", f"https://x/{i}")
            for i in range(200)]
    msgs = build_digests(many, header="H", limit=3900)
    assert "part 1/" in msgs[0]


def test_build_digests_empty_returns_no_messages():
    assert build_digests([], header="H") == []


@patch("lootscout.channels.telegram.requests.post")
def test_notify_digest_sends_one_message_for_small_list(mock_post):
    mock_post.return_value = MagicMock(raise_for_status=MagicMock())
    ch = TelegramChannel(token="123:abc", chat_id="555")
    ch.notify_digest([g(1, "Eets"), g(2, "Foo")], header="Live:")
    assert mock_post.call_count == 1
    payload = mock_post.call_args.kwargs["json"]
    assert payload["chat_id"] == "555"
    assert payload["parse_mode"] == "HTML"
    assert payload["disable_web_page_preview"] is True
    assert "Eets" in payload["text"] and "Foo" in payload["text"]


@patch("lootscout.channels.telegram.requests.post")
def test_notify_digest_sends_multiple_messages_for_big_backlog(mock_post):
    mock_post.return_value = MagicMock(raise_for_status=MagicMock())
    ch = TelegramChannel(token="123:abc", chat_id="555")
    many = [g(i, f"Game number {i} with a reasonably long title", f"https://x/{i}")
            for i in range(200)]
    ch.notify_digest(many, header="Live:")
    assert mock_post.call_count > 1             # one POST per chunk

from unittest.mock import patch, MagicMock
from lootscout.channels.base import Channel, Giveaway
from lootscout.channels.email import EmailChannel
from lootscout.channels.rss import RssChannel
from lootscout.channels.telegram import TelegramChannel


def g(i, t): return Giveaway(i, t, "$9", "", "d", "https://u", "N/A", "PC")


def test_protocol_requires_notify_digest():
    assert hasattr(Channel, "notify_digest")


@patch("lootscout.channels.email.smtplib.SMTP_SSL")
def test_email_digest_sends_one_email_with_links(mock_smtp):
    server = MagicMock()
    mock_smtp.return_value.__enter__.return_value = server
    ch = EmailChannel(user="a@gmail.com", password="pw", recipient="me@x.com")
    ch.notify_digest([g(1, "Eets"), g(2, "Foo")], header="Live:")
    server.send_message.assert_called_once()      # one email, not one per game
    sent = server.send_message.call_args.args[0]
    body = sent.get_content()
    assert "Eets" in body and "Foo" in body
    assert "https://u" in body                     # link present


@patch("lootscout.channels.email.smtplib.SMTP_SSL")
def test_email_digest_skips_when_empty(mock_smtp):
    EmailChannel("a@gmail.com", "pw", "me@x.com").notify_digest([], header="H")
    mock_smtp.assert_not_called()


def test_rss_digest_is_noop(tmp_path):
    RssChannel(tmp_path / "f.xml", "https://x").notify_digest([g(1, "Eets")], header="H")  # no raise


def test_all_real_channels_satisfy_protocol(tmp_path):
    chans = [
        TelegramChannel("t", "c"),
        EmailChannel("u", "p", "r"),
        RssChannel(tmp_path / "f.xml", "https://x"),
    ]
    for c in chans:
        assert isinstance(c, Channel)

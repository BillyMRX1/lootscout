from unittest.mock import patch, MagicMock
from free_checker.channels.email import EmailChannel
from free_checker.channels.base import Giveaway

def g(i, t): return Giveaway(i, t, "$9", "", "d", "https://u", "N/A", "PC")

@patch("free_checker.channels.email.smtplib.SMTP_SSL")
def test_notify_new_sends_one_email_via_smtp(mock_smtp):
    server = MagicMock()
    mock_smtp.return_value.__enter__.return_value = server
    ch = EmailChannel(user="a@gmail.com", password="pw", recipient="me@x.com")
    ch.notify_new([g(1, "Eets"), g(2, "Foo")])
    server.login.assert_called_once_with("a@gmail.com", "pw")
    server.send_message.assert_called_once()  # one digest email, not one per game

@patch("free_checker.channels.email.smtplib.SMTP_SSL")
def test_notify_new_skips_when_empty(mock_smtp):
    EmailChannel("a@gmail.com", "pw", "me@x.com").notify_new([])
    mock_smtp.assert_not_called()

from __future__ import annotations
import smtplib
from email.message import EmailMessage
from .base import Giveaway


class EmailChannel:
    name = "email"

    def __init__(self, user: str, password: str, recipient: str,
                 host: str = "smtp.gmail.com", port: int = 465):
        self.user = user
        self.password = password
        self.recipient = recipient
        self.host = host
        self.port = port

    def notify_new(self, games: list[Giveaway]) -> None:
        if not games:
            return
        msg = EmailMessage()
        msg["Subject"] = f"🎮 {len(games)} new free game(s)"
        msg["From"] = self.user
        msg["To"] = self.recipient
        lines = [f"- {x.title} ({x.worth}) [{x.platforms}]\n  {x.url}" for x in games]
        msg.set_content("New free game giveaways:\n\n" + "\n\n".join(lines))
        with smtplib.SMTP_SSL(self.host, self.port) as server:
            server.login(self.user, self.password)
            server.send_message(msg)

    def notify_digest(self, games: list[Giveaway], header: str) -> None:
        if not games:
            return
        msg = EmailMessage()
        msg["Subject"] = f"🎮 {len(games)} free game(s) to keep"
        msg["From"] = self.user
        msg["To"] = self.recipient
        lines = [f"- {x.title} ({x.worth}) [{x.platforms}]\n  {x.url}" for x in games]
        msg.set_content(header + "\n\n" + "\n\n".join(lines))
        with smtplib.SMTP_SSL(self.host, self.port) as server:
            server.login(self.user, self.password)
            server.send_message(msg)

    def write_full(self, games: list[Giveaway]) -> None:
        pass  # push-only

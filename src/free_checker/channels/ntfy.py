from __future__ import annotations
import requests
from .base import Giveaway


class NtfyChannel:
    name = "ntfy"

    def __init__(self, topic: str, server: str = "https://ntfy.sh", token: str | None = None):
        self.topic = topic
        self.server = server.rstrip("/")
        self.token = token

    def _headers(self, title: str, click: str) -> dict:
        h = {"Title": title, "Tags": "video_game", "Click": click}
        if self.token:
            h["Authorization"] = f"Bearer {self.token}"
        return h

    def notify_new(self, games: list[Giveaway]) -> None:
        url = f"{self.server}/{self.topic}"
        for game in games:
            body = f"{game.title} — {game.worth}\n{game.platforms}"
            resp = requests.post(
                url, data=body.encode("utf-8"),
                headers=self._headers(f"🎮 Free: {game.title}", game.url),
                timeout=20,
            )
            resp.raise_for_status()

    def write_full(self, games: list[Giveaway]) -> None:
        pass  # ntfy is push-only

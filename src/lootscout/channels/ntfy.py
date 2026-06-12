from __future__ import annotations
import requests
from .base import Giveaway


class NtfyChannel:
    name = "ntfy"

    def __init__(self, topic: str, server: str = "https://ntfy.sh", token: str | None = None):
        self.topic = topic
        self.server = server.rstrip("/")
        self.token = token

    def _headers(self) -> dict:
        # Only ASCII-safe values belong in HTTP headers (latin-1 encoded by
        # urllib3). Unicode title/message go in the JSON body instead.
        h = {}
        if self.token:
            h["Authorization"] = f"Bearer {self.token}"
        return h

    def notify_new(self, games: list[Giveaway]) -> None:
        for game in games:
            payload = {
                "topic": self.topic,
                "title": f"🎮 Free: {game.title}",
                "message": f"{game.worth} — {game.platforms}",
                "click": game.url,
                "tags": ["video_game"],
            }
            resp = requests.post(
                self.server, json=payload, headers=self._headers(), timeout=20
            )
            resp.raise_for_status()

    def write_full(self, games: list[Giveaway]) -> None:
        pass  # ntfy is push-only

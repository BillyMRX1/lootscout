from __future__ import annotations
import requests
from .base import Giveaway


class TelegramChannel:
    name = "telegram"

    def __init__(self, token: str, chat_id: str):
        self.token = token
        self.chat_id = chat_id

    def _api(self, method: str) -> str:
        return f"https://api.telegram.org/bot{self.token}/{method}"

    def notify_new(self, games: list[Giveaway]) -> None:
        for game in games:
            text = (f"🎮 <b>{game.title}</b> — {game.worth}\n"
                    f"{game.platforms}\n{game.url}")
            resp = requests.post(
                self._api("sendMessage"),
                json={"chat_id": self.chat_id, "text": text,
                      "parse_mode": "HTML", "disable_web_page_preview": False},
                timeout=20,
            )
            resp.raise_for_status()

    def write_full(self, games: list[Giveaway]) -> None:
        pass  # push-only

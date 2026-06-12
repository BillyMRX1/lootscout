from __future__ import annotations
import html
import requests
from .base import Giveaway

# Telegram hard-caps a message at 4096 chars; stay safely under it.
DIGEST_LIMIT = 3900


def build_digest(games: list[Giveaway], header: str, limit: int = DIGEST_LIMIT) -> str:
    """One consolidated HTML message: header + clickable title per giveaway.

    Truncates with an '…and N more' tail if it would exceed `limit`.
    """
    lines = [header, ""]
    for i, gv in enumerate(games):
        title = html.escape(gv.title)
        worth = html.escape(gv.worth)
        url = html.escape(gv.url)
        line = f'🎮 <a href="{url}">{title}</a> — {worth}'
        tail = f"…and {len(games) - i} more"
        if len("\n".join(lines + [line, tail])) > limit:
            lines.append(tail)
            break
        lines.append(line)
    return "\n".join(lines)


class TelegramChannel:
    name = "telegram"

    def __init__(self, token: str, chat_id: str):
        self.token = token
        self.chat_id = chat_id

    def _api(self, method: str) -> str:
        return f"https://api.telegram.org/bot{self.token}/{method}"

    def notify_new(self, games: list[Giveaway]) -> None:
        for game in games:
            title = html.escape(game.title)
            worth = html.escape(game.worth)
            platforms = html.escape(game.platforms)
            text = (f"🎮 <b>{title}</b> — {worth}\n"
                    f"{platforms}\n{game.url}")
            resp = requests.post(
                self._api("sendMessage"),
                json={"chat_id": self.chat_id, "text": text,
                      "parse_mode": "HTML", "disable_web_page_preview": False},
                timeout=20,
            )
            resp.raise_for_status()

    def notify_digest(self, games: list[Giveaway], header: str) -> None:
        if not games:
            return
        resp = requests.post(
            self._api("sendMessage"),
            json={"chat_id": self.chat_id, "text": build_digest(games, header),
                  "parse_mode": "HTML", "disable_web_page_preview": True},
            timeout=20,
        )
        resp.raise_for_status()

    def write_full(self, games: list[Giveaway]) -> None:
        pass  # push-only

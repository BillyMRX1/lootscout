from __future__ import annotations
import html
import requests
from .base import Giveaway

# Telegram hard-caps a message at 4096 chars; stay safely under it.
DIGEST_LIMIT = 3900


def _digest_line(gv: Giveaway) -> str:
    title = html.escape(gv.title)
    worth = html.escape(gv.worth)
    url = html.escape(gv.url)
    return f'🎮 <a href="{url}">{title}</a> — {worth}'


def build_digests(games: list[Giveaway], header: str, limit: int = DIGEST_LIMIT) -> list[str]:
    """Consolidated HTML digest split across as many messages as needed so every
    giveaway is included and no message exceeds `limit` (no truncation/dropping).

    A single message keeps the plain header; when split, each carries a
    '(part i/n)' suffix.
    """
    if not games:
        return []
    lines = [_digest_line(gv) for gv in games]
    # Greedily pack lines into chunks. Reserve room for the header + part suffix.
    reserve = len(header) + len(" (part 99/99)") + 2
    chunks: list[list[str]] = []
    cur: list[str] = []
    cur_len = 0
    for line in lines:
        add = len(line) + 1
        if cur and reserve + cur_len + add > limit:
            chunks.append(cur)
            cur, cur_len = [], 0
        cur.append(line)
        cur_len += add
    if cur:
        chunks.append(cur)

    n = len(chunks)
    out = []
    for i, chunk in enumerate(chunks, 1):
        head = header if n == 1 else f"{header} (part {i}/{n})"
        out.append("\n".join([head, "", *chunk]))
    return out


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
        for text in build_digests(games, header):
            resp = requests.post(
                self._api("sendMessage"),
                json={"chat_id": self.chat_id, "text": text,
                      "parse_mode": "HTML", "disable_web_page_preview": True},
                timeout=20,
            )
            resp.raise_for_status()

    def write_full(self, games: list[Giveaway]) -> None:
        pass  # push-only

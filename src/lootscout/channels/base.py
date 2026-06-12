from __future__ import annotations
from dataclasses import dataclass
from typing import Protocol, runtime_checkable


@dataclass(frozen=True)
class Giveaway:
    id: int
    title: str
    worth: str
    image: str
    description: str
    url: str
    end_date: str        # may be the literal string "N/A"
    platforms: str

    @classmethod
    def from_api(cls, raw: dict) -> "Giveaway":
        return cls(
            id=int(raw["id"]),
            title=raw.get("title", ""),
            worth=raw.get("worth", ""),
            image=raw.get("image", ""),
            description=raw.get("description", ""),
            url=raw.get("open_giveaway_url", ""),
            end_date=raw.get("end_date", "N/A"),
            platforms=raw.get("platforms", ""),
        )


@runtime_checkable
class Channel(Protocol):
    name: str
    def notify_new(self, games: list[Giveaway]) -> None: ...   # push: on NEW games
    def write_full(self, games: list[Giveaway]) -> None: ...   # pull: ALL current

from __future__ import annotations
import requests
from .channels.base import Giveaway

API_BASE = "https://www.gamerpower.com/api/filter"


def build_url(platforms: list[str], types: list[str]) -> str:
    plat = ".".join(platforms)
    typ = ".".join(types)
    return f"{API_BASE}?platform={plat}&type={typ}"


def parse(raw_list: list[dict]) -> list[Giveaway]:
    return [Giveaway.from_api(item) for item in raw_list]


def fetch(platforms: list[str], types: list[str], timeout: int = 20) -> list[Giveaway]:
    url = build_url(platforms, types)
    resp = requests.get(url, timeout=timeout, headers={"User-Agent": "lootscout/0.1"})
    resp.raise_for_status()
    return parse(resp.json())

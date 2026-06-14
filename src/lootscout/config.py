from __future__ import annotations
import os
import tomllib
from dataclasses import dataclass
from pathlib import Path

VALID_CHANNELS = {"email", "telegram", "rss"}


class ConfigError(Exception):
    pass


@dataclass
class Config:
    platforms: list[str]
    types: list[str]
    enabled: list[str]
    data: dict
    env: dict

    def section(self, name: str) -> dict:
        return self.data.get(name, {})

    def require_secret(self, key: str) -> str:
        val = self.env.get(key)
        if not val:
            raise ConfigError(f"Missing required secret: {key} (set it in .env)")
        return val


def load(config_path: Path, env: dict | None = None) -> Config:
    env = env if env is not None else dict(os.environ)
    raw = tomllib.loads(Path(config_path).read_text())
    enabled = raw.get("enabled", [])
    unknown = set(enabled) - VALID_CHANNELS
    if unknown:
        raise ConfigError(f"Unknown channel(s) in 'enabled': {sorted(unknown)}")
    return Config(
        platforms=raw.get("platforms", ["pc"]),
        types=_load_types(raw),
        enabled=enabled,
        data=raw,
        env=env,
    )


def _load_types(raw: dict) -> list[str]:
    """Read giveaway types as a list, accepting the legacy single `type` string
    (which may itself be period-joined, e.g. "game.loot")."""
    types = raw.get("types")
    if types:
        return list(types)
    legacy = raw.get("type", "game")
    return legacy.split(".") if isinstance(legacy, str) else ["game"]

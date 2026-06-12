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
    type: str
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
        type=raw.get("type", "game"),
        enabled=enabled,
        data=raw,
        env=env,
    )

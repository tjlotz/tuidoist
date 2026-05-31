"""Configuration management for Tuidoist.

Reads and writes ~/.config/tuidoist/config.toml with restricted file permissions.
"""

from __future__ import annotations

import os
import tomllib
from dataclasses import dataclass
from pathlib import Path

CONFIG_DIR = Path.home() / ".config" / "tuidoist"
CONFIG_FILE = CONFIG_DIR / "config.toml"


@dataclass
class Config:
    api_token: str = ""

    @property
    def is_authenticated(self) -> bool:
        return bool(self.api_token)


def load() -> Config:
    """Load config from disk. Returns default config if file doesn't exist or is malformed."""
    if not CONFIG_FILE.exists():
        return Config()

    try:
        with open(CONFIG_FILE, "rb") as f:
            data = tomllib.load(f)
    except (tomllib.TOMLDecodeError, OSError):
        return Config()

    return Config(
        api_token=data.get("auth", {}).get("api_token", ""),
    )


def save(config: Config) -> None:
    """Write config to disk with 600 permissions."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)

    content = f'[auth]\napi_token = "{config.api_token}"\n'

    # Write to temp file then rename for atomicity
    tmp = CONFIG_FILE.with_suffix(".tmp")
    fd = os.open(str(tmp), os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    try:
        os.write(fd, content.encode())
    finally:
        os.close(fd)
    tmp.rename(CONFIG_FILE)

from __future__ import annotations

import os
from dataclasses import dataclass


def _env_bool(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "y"}


def _env_int(name: str, default: int) -> int:
    raw = os.getenv(name)
    if raw is None:
        return default
    try:
        return int(raw)
    except ValueError:
        return default


@dataclass
class Settings:
    avito_login: str
    avito_password: str
    cookies_path: str
    headless: bool
    dry_run: bool
    max_replies_per_run: int
    min_delay_s: int
    max_delay_s: int


def load_settings() -> Settings:
    return Settings(
        avito_login=os.getenv("AVITO_LOGIN", ""),
        avito_password=os.getenv("AVITO_PASSWORD", ""),
        cookies_path=os.getenv("AVITO_COOKIES_PATH", ".cookies/avito_cookies.json"),
        headless=_env_bool("AVITO_HEADLESS", True),
        dry_run=_env_bool("AVITO_DRY_RUN", True),
        max_replies_per_run=_env_int("AVITO_MAX_REPLIES_PER_RUN", 10),
        min_delay_s=_env_int("AVITO_MIN_DELAY_S", 2),
        max_delay_s=_env_int("AVITO_MAX_DELAY_S", 5),
    )


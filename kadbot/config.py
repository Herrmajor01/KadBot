"""
Единый модуль конфигурации приложения.
Читает переменные из окружения/.env и предоставляет доступ в виде объекта.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Optional

from dotenv import load_dotenv  # type: ignore


@dataclass
class Config:
    aspro_api_key: str
    aspro_company: str
    user_id: str
    user_name: str
    aspro_event_calendar_id: Optional[int]
    database_url: str
    documents_dir: str
    log_level: str
    browser_timeout: int
    browser_retries: int


_CONFIG: Optional[Config] = None


def get_config() -> Config:
    global _CONFIG
    if _CONFIG is not None:
        return _CONFIG

    load_dotenv()

    api_key = os.getenv("ASPRO_API_KEY", "").strip()
    company = os.getenv("ASPRO_COMPANY", "").strip()
    user_id = os.getenv("USERID", "").strip()
    user_name = os.getenv("USER_NAME", "").strip()
    # Уберем кавычки вокруг USER_NAME, если есть
    if (user_name.startswith('"') and user_name.endswith('"')) or (
        user_name.startswith("'") and user_name.endswith("'")
    ):
        user_name = user_name[1:-1]

    try:
        cal_id_env = os.getenv("ASPRO_EVENT_CALENDAR_ID")
        cal_id = int(cal_id_env) if cal_id_env else None
    except ValueError:
        cal_id = None

    db_url = os.getenv("DATABASE_URL", "sqlite:///kad_cases.db").strip()
    docs_dir = os.getenv("DOCUMENTS_DIR", os.path.join(os.getcwd(), "documents")).strip()
    log_level = os.getenv("LOG_LEVEL", "INFO").strip().upper()
    try:
        browser_timeout = int(os.getenv("BROWSER_TIMEOUT", "30"))
    except ValueError:
        browser_timeout = 30
    try:
        browser_retries = int(os.getenv("BROWSER_RETRIES", "3"))
    except ValueError:
        browser_retries = 3

    _CONFIG = Config(
        aspro_api_key=api_key,
        aspro_company=company,
        user_id=user_id,
        user_name=user_name,
        aspro_event_calendar_id=cal_id,
        database_url=db_url,
        documents_dir=docs_dir,
        log_level=log_level,
        browser_timeout=browser_timeout,
        browser_retries=browser_retries,
    )
    return _CONFIG


def reset_config() -> None:
    """Сбрасывает кеш конфигурации (для тестов)."""
    global _CONFIG
    _CONFIG = None

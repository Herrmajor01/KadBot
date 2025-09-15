"""
Единая настройка логирования с ротацией.
"""

import logging
from logging.handlers import RotatingFileHandler
from typing import Optional


def configure_logging(level: str = "INFO", logfile: str = "kad_parser.log") -> None:
    """
    Настраивает корневой логгер, если он ещё не настроен.
    - Ротация логов до ~5MB, 5 бэкапов
    - Потоковый вывод на консоль
    """
    root = logging.getLogger()
    if root.handlers:
        # Уже настроен где-то ещё — не дублировать
        return

    level_num: int = getattr(logging, level.upper(), logging.INFO)
    root.setLevel(level_num)

    fmt = logging.Formatter("%(asctime)s - %(levelname)s - %(name)s - %(message)s")

    file_handler = RotatingFileHandler(logfile, maxBytes=5 * 1024 * 1024, backupCount=5)
    file_handler.setFormatter(fmt)
    file_handler.setLevel(level_num)

    console = logging.StreamHandler()
    console.setFormatter(fmt)
    console.setLevel(level_num)

    root.addHandler(file_handler)
    root.addHandler(console)

"""
Утилитный модуль с общими функциями для парсинга и скачивания документов.
"""

import json
import logging
import os
import random
import socket
import time
from typing import Any, Dict, Optional

try:
    import undetected_chromedriver as uc  # type: ignore
    from selenium.webdriver.common.by import By  # type: ignore
    from selenium.webdriver.support import (
        expected_conditions as EC,  # type: ignore
    )
    from selenium.webdriver.support.ui import WebDriverWait  # type: ignore
except ImportError as e:
    raise ImportError(f"Required modules are missing: {e}")

# Список User-Agent для эмуляции разных браузеров
USER_AGENTS = [
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 "
    "(KHTML, like Gecko) Version/17.0 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:128.0) "
    "Gecko/20100101 Firefox/128.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Edge/126.0.0.0",
]


def save_progress(case_number: str, index: int, filename: str) -> None:
    """
    Сохраняет прогресс обработки в JSON-файл.

    Args:
        case_number: Номер последнего обработанного дела
        index: Индекс последнего обработанного дела в списке
        filename: Имя файла для сохранения прогресса
    """
    progress = {"last_case_number": case_number, "last_index": index}
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(progress, f, ensure_ascii=False)
    logging.info(
        f"Прогресс сохранён в {filename}: {case_number}, " f"индекс {index}"
    )


def load_progress(filename: str) -> Optional[Dict[str, Any]]:
    """
    Загружает прогресс обработки из JSON-файла.

    Args:
        filename: Имя файла прогресса

    Returns:
        Dict[str, Any]: Словарь с номером дела и индексом или None,
        если файл не существует
    """
    if os.path.exists(filename):
        try:
            with open(filename, "r", encoding="utf-8") as f:
                progress = json.load(f)
            if "last_case_number" in progress and "last_index" in progress:
                return progress
            logging.warning(f"Некорректный формат файла прогресса: {filename}")
        except json.JSONDecodeError:
            logging.error(f"Ошибка чтения файла прогресса: {filename}")
    return None


def clear_progress(filename: str) -> None:
    """
    Удаляет файл прогресса.

    Args:
        filename: Имя файла прогресса
    """
    if os.path.exists(filename):
        os.remove(filename)
        logging.info(f"Файл прогресса удалён: {filename}")


def get_driver(retries: int = 3, timeout: int = 30) -> Optional[uc.Chrome]:
    """
    Инициализирует и настраивает Chrome драйвер для парсинга.

    Args:
        retries: Количество попыток инициализации драйвера
        timeout: Таймаут для сетевых операций

    Returns:
        uc.Chrome: Настроенный Chrome драйвер или None при ошибке

    Raises:
        Exception: Если не удалось инициализировать драйвер после всех попыток
    """
    options = uc.ChromeOptions()
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--disable-infobars")
    options.add_argument("--lang=ru-RU")
    options.add_argument("--window-size=1280,900")
    options.add_argument(f"--user-agent={random.choice(USER_AGENTS)}")
    options.add_argument("--disable-web-security")
    options.add_argument("--disable-site-isolation-trials")

    socket.setdefaulttimeout(timeout)

    for attempt in range(retries):
        try:
            logging.info(
                f"Попытка инициализации Chrome драйвера "
                f"({attempt + 1}/{retries})"
            )
            driver = uc.Chrome(options=options, use_subprocess=True)
            logging.info("Chrome драйвер успешно инициализирован")
            driver.get("https://kad.arbitr.ru")
            WebDriverWait(driver, timeout).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            logging.info("Страница kad.arbitr.ru прогружена")
            return driver
        except Exception as e:
            logging.error(f"Ошибка инициализации Chrome драйвера: {e}")
            if attempt < retries - 1:
                time.sleep(2)
            else:
                logging.error("Не удалось инициализировать Chrome драйвер")
                raise Exception("Не удалось инициализировать Chrome драйвер")
    return None


def simulate_mouse_movement(driver: uc.Chrome) -> None:
    """
    Эмулирует движение мыши для имитации человеческого поведения.

    Args:
        driver: Chrome драйвер для выполнения JavaScript
    """
    try:
        driver.execute_script(
            """
            function moveMouse(x, y) {
                const event = new MouseEvent('mousemove', {
                    clientX: x,
                    clientY: y,
                    bubbles: true
                });
                document.dispatchEvent(event);
            }
            moveMouse(Math.random() * 1200, Math.random() * 800);
        """
        )
        time.sleep(random.uniform(0.1, 0.3))
    except Exception as e:
        logging.info(f"Ошибка эмуляции движения мыши: {e}")

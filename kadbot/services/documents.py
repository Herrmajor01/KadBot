"""
Модуль для скачивания документов по ссылкам из базы данных и выполнения OCR.
"""

import logging
import os
import pickle
import random
import re
import shutil
import time
from typing import Optional

import pyautogui  # type: ignore
import pytesseract  # type: ignore
from pdf2image import convert_from_path  # type: ignore
from selenium.webdriver.common.by import By  # type: ignore
from selenium.webdriver.support import (
    expected_conditions as EC,  # type: ignore
)
from selenium.webdriver.support.ui import WebDriverWait  # type: ignore
from dotenv import load_dotenv  # type: ignore
from tqdm import tqdm  # type: ignore

from kadbot.db.models import Chronology
from kadbot.db.session import Session
from kadbot.utils import (
    clear_progress,
    get_driver,
    load_progress,
    save_progress,
    simulate_mouse_movement,
)

logging.basicConfig(
    filename="kad_parser.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)

# Загружаем конфигурацию из .env
load_dotenv()

# Директория документов по умолчанию берётся из окружения
DEFAULT_DOCUMENTS_DIR = os.getenv(
    "DOCUMENTS_DIR", os.path.join(os.getcwd(), "documents")
)


def clean_event_title(event_title: str) -> str:
    """
    Очистка названия документа от недопустимых символов.

    Args:
        event_title: Исходное название события

    Returns:
        str: Очищенное название документа
    """
    if not event_title:
        return "Document"
    cleaned = re.sub(r"[^\w\s-]", "", event_title.strip()).replace(" ", "_")
    return cleaned if cleaned else "Document"


def format_case_number(case_number: str) -> str:
    """
    Форматирование номера дела, например, А32-29491/2023 -> А32-29491_2023.

    Args:
        case_number: Номер дела

    Returns:
        str: Отформатированный номер дела
    """
    return case_number.replace("/", "_")


def download_document(
    driver,
    url: str,
    case_number: str,
    event_title: str,
    event_date: str,
    case_participants=None,
    output_dir: str = DEFAULT_DOCUMENTS_DIR,
) -> Optional[str]:
    """
    Скачивает документ по ссылке и выполняет OCR.

    Args:
        driver: Chrome драйвер
        url: Ссылка на документ
        case_number: Номер дела
        event_title: Название события
        event_date: Дата события
        case_participants: Участники дела
        output_dir: Папка для сохранения документов

    Returns:
        str: Путь к сохраненному файлу или None при ошибке
    """
    try:
        os.makedirs(output_dir, exist_ok=True)
        logging.info(
            f"Попытка загрузки документа для дела {case_number}: {url}"
        )

        # Устанавливаем папку загрузки (дублируем prefs через DevTools как fallback)
        download_dir = os.path.abspath(output_dir)
        try:
            driver.command_executor._commands["send_command"] = (
                "POST",
                "/session/$sessionId/chromium/send_command",
            )
            params = {
                "cmd": "Page.setDownloadBehavior",
                "params": {"behavior": "allow", "downloadPath": download_dir},
            }
            driver.execute("send_command", params)
        except Exception:
            pass

        # Загружаем cookies
        if os.path.exists("cookies.pkl"):
            cookies = pickle.load(open("cookies.pkl", "rb"))
            driver.get("https://kad.arbitr.ru")
            for cookie in cookies:
                driver.add_cookie(cookie)
            logging.info("Cookies загружены из cookies.pkl")

        # Эмуляция человеческого поведения
        for _ in range(2):
            x, y = random.randint(50, 1200), random.randint(50, 1200)
            driver.execute_script(f"window.scrollTo({x}, {y});")
            simulate_mouse_movement(driver)
            time.sleep(random.uniform(0.5, 1.0))
        driver.execute_script("window.scrollTo(0, 0);")
        time.sleep(random.uniform(0.5, 1.0))

        # Загружаем страницу с документом
        driver.get(url)
        time.sleep(random.uniform(3.0, 5.0))

        # Формируем имя файла (конечное имя; реальное имя загрузки может отличаться)
        event_title_clean = clean_event_title(event_title)
        case_number_clean = format_case_number(case_number)
        target_file_name = f"{event_title_clean}_{case_number_clean}.pdf"
        target_path = os.path.join(output_dir, target_file_name)

        # Предпочтительный путь: полагаться на автоскачивание в download_dir
        # Ждем появления .crdownload или .pdf в output_dir
        timeout = 60
        start_time = time.time()
        found_path = None
        while time.time() - start_time < timeout:
            for f in os.listdir(download_dir):
                if f.endswith(".crdownload") or f.endswith(".pdf"):
                    candidate = os.path.join(download_dir, f)
                    # Игнорируем временные, не относящиеся к нашему кейсу файлы по времени
                    found_path = candidate
                    break
            if found_path:
                # Если ещё идёт загрузка — ждём завершения
                if found_path.endswith(".crdownload"):
                    time.sleep(1)
                    continue
                else:
                    break
            time.sleep(1)

        if not found_path:
            logging.error(
                f"Не удалось обнаружить загруженный файл для дела {case_number} в {download_dir}"
            )
            return None

        # Переименовываем итоговый файл под целевое имя
        if found_path != target_path:
            try:
                shutil.move(found_path, target_path)
            except Exception:
                # Если не удалось переместить (например, одинаковые имена), просто используем найденный путь
                target_path = found_path

        if not os.path.exists(target_path):
            logging.error(
                f"Файл не был загружен для дела {case_number}: {target_path}"
            )
            print(f"Ошибка: Файл не был загружен для дела {case_number}.")
            return None

        logging.info(f"Документ для дела {case_number} сохранен в {target_path}")

        # OCR
        try:
            images = convert_from_path(target_path, dpi=400)
            text = ""
            for i, image in enumerate(images):
                text += pytesseract.image_to_string(
                    image, lang="rus", config="--psm 6 --oem 3"
                )
                logging.info(
                    f"OCR для страницы {i+1} дела {case_number}: "
                    f"{text[:100]}..."
                )
            with open(f"{target_path}.txt", "w", encoding="utf-8") as f:
                f.write(text)
            logging.info(f"OCR текст сохранен в {target_path}.txt")
        except Exception as e:
            logging.error(f"Ошибка OCR для дела {case_number}: {e}")
            print(f"Ошибка OCR для дела {case_number}: {e}")

        return target_path
    except Exception as e:
        logging.error(
            f"Ошибка скачивания документа для дела {case_number}: {e}"
        )
        print(f"Ошибка скачивания документа для дела {case_number}: {e}")
        return None


def download_documents(
    batch_size: int = 10, pause_between_batches: int = 30, resume: bool = False
) -> None:
    """
    Скачивает документы по ссылкам из базы данных.

    Args:
        batch_size: Размер пакета документов для обработки
        pause_between_batches: Пауза между пакетами в секундах
        resume: Если True, возобновляет скачивание с последнего документа
    """
    session = Session()
    processed_documents = 0
    driver = None
    start_index = 0

    try:
        documents = (
            session.query(Chronology)
            .filter(Chronology.doc_link.isnot(None), Chronology.doc_link != "")
            .all()
        )
        if not documents:
            logging.warning("Нет документов для обработки в базе данных.")
            print(
                "Предупреждение: Нет документов для обработки в базе данных. "
                "Запустите parser.py для сбора данных."
            )
            return

        logging.info(
            f"Найдено {len(documents)} записей хронологии с документами"
        )
        print(f"Найдено {len(documents)} документов для обработки.")

        if resume:
            progress = load_progress("download_progress.json")
            if progress:
                last_case_number = progress.get("last_case_number")
                start_index = progress.get("last_index", 0)
                logging.info(
                    f"Возобновление скачивания с дела {last_case_number} "
                    f"(индекс {start_index})"
                )
                documents = documents[start_index:]
            else:
                logging.info(
                    "Файл прогресса скачивания не найден, начинаем с начала"
                )
                start_index = 0
                documents = documents
        else:
            clear_progress("download_progress.json")

        driver = get_driver()

        with tqdm(
            total=len(documents), desc="Обработка документов", unit="документ"
        ) as pbar:
            for i in range(0, len(documents), batch_size):
                batch = documents[i : i + batch_size]
                logging.info(
                    f"Обработка пакета документов {i+1+start_index}-"
                    f"{min(i+batch_size+start_index, len(documents)+start_index)} "
                    f"из {len(documents)+start_index}"
                )
                print(
                    "Обработка пакета "
                    f"{i+1+start_index}-"
                    f"{min(i+batch_size+start_index, len(documents)+start_index)} "
                    f"из {len(documents)+start_index}"
                )

                for index, doc in enumerate(batch, start=i + start_index):
                    case_number = doc.case_number
                    doc_link = doc.doc_link
                    event_title = doc.event_title
                    event_date = doc.event_date
                    case_participants = getattr(doc, "case_participants", None)
                    try:
                        if doc_link.startswith(DEFAULT_DOCUMENTS_DIR):
                            logging.info(
                                "Документ для дела "
                                f"{case_number} уже сохранен локально: {doc_link}"
                            )
                            print(
                                f"Документ для дела {case_number} уже сохранен."
                            )
                            pbar.update(1)
                            continue

                        file_path = download_document(
                            driver,
                            doc_link,
                            case_number,
                            event_title,
                            event_date,
                            case_participants,
                        )
                        if file_path:
                            logging.info(
                                f"Сохранен документ для дела {case_number}: "
                                f"{file_path}"
                            )
                            print(
                                f"Сохранен документ для дела {case_number}: "
                                f"{file_path}"
                            )
                            processed_documents += 1
                        save_progress(
                            case_number, index, "download_progress.json"
                        )
                        pbar.update(1)
                    except Exception as e:
                        logging.error(
                            f"Ошибка обработки документа для дела "
                            f"{case_number}: {e}"
                        )
                        print(
                            f"Ошибка обработки документа для дела "
                            f"{case_number}: {e}"
                        )
                        pbar.update(1)
                        continue

                if i + batch_size < len(documents):
                    logging.info(
                        f"Пауза {pause_between_batches} секунд перед "
                        f"следующим пакетом"
                    )
                    time.sleep(pause_between_batches)

        logging.info(
            f"Завершена обработка {processed_documents} из {len(documents)} "
            f"документов"
        )
        print(
            f"Завершена обработка {processed_documents} из {len(documents)} "
            f"документов"
        )
        clear_progress("download_progress.json")
    except KeyboardInterrupt:
        logging.info("Процесс скачивания прерван пользователем")
        print("Процесс скачивания прерван пользователем")
    except Exception as e:
        logging.error(f"Критическая ошибка в download_documents: {e}")
        print(f"Критическая ошибка: {e}. Проверьте kad_parser.log.")
    finally:
        if driver:
            driver.quit()
            logging.info("Chrome драйвер закрыт")
        session.close()
        logging.info("Сессия базы данных закрыта")


if __name__ == "__main__":
    print("Запуск скачивания документов...")
    download_documents()
    print("Обработка завершена.")

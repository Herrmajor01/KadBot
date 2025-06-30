"""
Модуль для парсинга дел с сайта kad.arbitr.ru.
Содержит функции для парсинга событий дел
 и синхронизации хронологии с базой данных.
"""
import logging
import random
import time
import traceback
from datetime import datetime
from typing import Any, Dict, Optional, Tuple

try:
    import undetected_chromedriver as uc  # type: ignore
    from selenium.common.exceptions import (  # type: ignore
        TimeoutException,
        WebDriverException,
    )
    from selenium.webdriver.common.by import By  # type: ignore
    from selenium.webdriver.support import (  # type: ignore
        expected_conditions as EC,  # type: ignore
    )
    from selenium.webdriver.support.ui import WebDriverWait  # type: ignore
    from tqdm import tqdm  # type: ignore
except ImportError as e:
    raise ImportError(f"Required modules are missing: {e}")

from crm_notify import send_case_update_comment
from db import Session, get_project_id_for_case
from models import Cases, Chronology
from utils import (
    clear_progress,
    get_driver,
    load_progress,
    save_progress,
    simulate_mouse_movement,
)

logging.basicConfig(
    filename="kad_parser.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)


def parse_date(date_str: str) -> Optional[datetime]:
    """
    Парсит строку даты в формате DD.MM.YYYY в объект datetime.

    Args:
        date_str: Строка с датой в формате DD.MM.YYYY

    Returns:
        datetime: Объект datetime или None при ошибке парсинга
    """
    try:
        return datetime.strptime(date_str, "%d.%m.%Y")
    except (ValueError, TypeError):
        return None


def get_case_events(
    driver: uc.Chrome,
    case_number: str
) -> Tuple[Optional[Dict[str, Any]], int]:
    """
    Получает события для конкретного дела с сайта kad.arbitr.ru.

    Args:
        driver: Chrome драйвер для парсинга
        case_number: Номер дела для парсинга

    Returns:
        Tuple: (данные события, количество событий) или (None, 0) при ошибке
    """
    for attempt in range(3):
        try:
            url = f"https://kad.arbitr.ru/Card?number={case_number}"
            driver.get(url)
            time.sleep(random.uniform(2.0, 5.0))
            logging.info(f"Загружена страница для дела {case_number}")

            # Проверка на блокировку
            if "Доступ к сервису ограничен" in driver.page_source:
                logging.error(f"IP заблокирован для дела {case_number}")
                with open(
                    f"error_{case_number.replace('/', '_')}.html",
                    "w",
                    encoding="utf-8"
                ) as f:
                    f.write(driver.page_source)
                return None, 0

            # Проверка на ограничение подписки
            if "Вы можете оформить подписку на 40 дел" in driver.page_source:
                logging.warning(
                    f"Доступ к хронологии ограничен из-за подписки для дела "
                    f"{case_number}")
                with open(
                    f"error_{case_number.replace('/', '_')}.html",
                    "w",
                    encoding="utf-8"
                ) as f:
                    f.write(driver.page_source)
                return {
                    "event_date": "",
                    "event_title": "Доступ ограничен (подписка)",
                    "event_author": "",
                    "event_publish": "",
                    "doc_link": ""
                }, 0

            # Эмуляция человеческого поведения (уменьшено до 3 прокруток)
            for _ in range(3):
                x, y = random.randint(50, 1200), random.randint(50, 1200)
                driver.execute_script(f"window.scrollTo({x}, {y});")
                simulate_mouse_movement(driver)
                time.sleep(random.uniform(0.5, 1.0))
            driver.execute_script("window.scrollTo(0, 0);")
            time.sleep(random.uniform(0.5, 1.0))

            # Переключение на вкладку "Судебные акты"
            try:
                tabs = WebDriverWait(driver, 8).until(
                    EC.presence_of_all_elements_located(
                        (By.CSS_SELECTOR, ".b-tab.js-tab"))
                )
                for tab in tabs:
                    if "Судебные акты" in tab.text:
                        driver.execute_script("arguments[0].click();", tab)
                        time.sleep(random.uniform(1.0, 2.0))
                        logging.info(
                            f"Переключено на вкладку 'Судебные акты' для дела "
                            f"{case_number}")
                        break
            except Exception as e:
                logging.info(
                    f"Не удалось переключиться на вкладку 'Судебные акты' "
                    f"для дела {case_number}: {e}")

            # Ожидание и клик по кнопке раскрытия хронологии
            try:
                collapse_btn = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable(
                        (By.CSS_SELECTOR, ".b-collapse.js-collapse"))
                )
                driver.execute_script(
                    "arguments[0].scrollIntoView(true);", collapse_btn)
                driver.execute_script("arguments[0].click();", collapse_btn)
                time.sleep(random.uniform(1.0, 2.0))
                logging.info(f"Раскрыта хронология для дела {case_number}")
            except TimeoutException:
                logging.warning(
                    f"Кнопка раскрытия хронологии (.b-collapse.js-collapse) "
                    f"не найдена для дела {case_number} после 10 секунд")
                with open(
                    f"error_{case_number.replace('/', '_')}.html",
                    "w",
                    encoding="utf-8"
                ) as f:
                    f.write(driver.page_source)
                return None, 0
            except Exception as e:
                logging.warning(
                    "Ошибка при клике на хронологию для дела "
                    f"{case_number}: {e}"
                )
                with open(
                    f"error_{case_number.replace('/', '_')}.html",
                    "w",
                    encoding="utf-8"
                ) as f:
                    f.write(driver.page_source)
                return None, 0

            # Ожидание элементов хронологии
            try:
                elements = WebDriverWait(driver, 20).until(
                    EC.presence_of_all_elements_located(
                        (By.CSS_SELECTOR, ".b-chrono-item.js-chrono-item"))
                )
            except TimeoutException:
                logging.warning(
                    f"Элементы хронологии (.b-chrono-item.js-chrono-item) "
                    f"не найдены для дела {case_number} после 20 секунд"
                )
                with open(
                    f"error_{case_number.replace('/', '_')}.html",
                    "w",
                    encoding="utf-8"
                ) as f:
                    f.write(driver.page_source)
                return None, 0

            events_count = len(elements)
            last_event = elements[0]

            def safe_sel(el, sel):
                """Безопасное извлечение текста из элемента."""
                try:
                    return el.find_element(By.CSS_SELECTOR, sel).text.strip()
                except Exception:
                    return ""

            doc_link = ""
            doc_links = last_event.find_elements(
                By.CSS_SELECTOR, "a.js-case-result-text--doc_link"
            )
            if doc_links:
                doc_link = doc_links[0].get_attribute("href")

            event_data = {
                "event_date": safe_sel(last_event, ".case-date"),
                "event_title": safe_sel(last_event, ".case-type"),
                "event_author": safe_sel(last_event, ".case-subject"),
                "event_publish": safe_sel(
                    last_event, ".b-case-publish_info"
                ).replace("Дата публикации:", "").strip(),
                "doc_link": doc_link
            }
            logging.info(
                f"Спарсено событие для дела {case_number}: "
                f"{event_data['event_date']}, {event_data['event_title']}"
            )
            return event_data, events_count
        except WebDriverException as e:
            logging.error(
                f"Ошибка парсинга дела {case_number} "
                f"(попытка {attempt + 1}/3): {str(e)}"
            )
            logging.error(f"Stacktrace: {traceback.format_exc()}")
            with open(
                f"error_{case_number.replace('/', '_')}.html",
                "w",
                encoding="utf-8"
            ) as f:
                f.write(driver.page_source)
            if attempt < 2:
                driver.refresh()
                time.sleep(random.uniform(3.0, 5.0))
            else:
                logging.error(
                    f"Не удалось получить события для дела {case_number} "
                    f"после 3 попыток"
                )
                return None, 0
    return None, 0


def sync_chronology(
    batch_size: int = 50,
    pause_between_batches: int = 120,
    resume: bool = False
) -> None:
    """
    Синхронизирует хронологию дел с сайта kad.arbitr.ru с базой данных.

    Обрабатывает дела пакетами, получает последние события и обновляет
    базу данных. При обнаружении новых событий отправляет уведомления в CRM.
    Поддерживает возобновление с последнего обработанного дела.

    Args:
        batch_size: Размер пакета дел для обработки
        pause_between_batches: Пауза между пакетами в секундах
        resume: Если True, возобновляет парсинг с последнего обработанного дела
    """
    session = Session()
    driver = get_driver()
    processed_cases = 0
    start_index = 0

    try:
        cases = session.query(Cases).all()
        logging.info(f"Найдено {len(cases)} дел для обработки")

        if resume:
            progress = load_progress("parser_progress.json")
            if progress:
                last_case_number = progress.get("last_case_number")
                start_index = progress.get("last_index", 0)
                logging.info(
                    f"Возобновление с дела {last_case_number} "
                    f"(индекс {start_index})")
                cases = cases[start_index:]
            else:
                logging.info("Файл прогресса не найден, начинаем с начала")
                start_index = 0
                cases = cases
        else:
            clear_progress("parser_progress.json")

        with tqdm(total=len(cases), desc="Обработка дел", unit="дело") as pbar:
            for i in range(0, len(cases), batch_size):
                batch = cases[i:i + batch_size]
                logging.info(
                    f"Обработка пакета дел {i+1+start_index}-"
                    f"{min(i+batch_size+start_index, len(cases)+start_index)} "
                    f"из {len(cases)+start_index}"
                )
                for index, case in enumerate(batch, start=i+start_index):
                    case_number = case.case_number
                    try:
                        db_event = session.query(Chronology).filter_by(
                            case_number=case_number
                        ).order_by(Chronology.id.desc()).first()
                        web_event, events_count = get_case_events(
                            driver, case_number
                        )
                        if not web_event:
                            logging.warning(
                                f"Не удалось получить события для дела "
                                f"{case_number}"
                            )
                            pbar.update(1)
                            continue

                        new_date = parse_date(web_event["event_date"])
                        if not db_event:
                            session.add(Chronology(
                                case_number=case_number,
                                event_date=web_event["event_date"],
                                event_title=web_event["event_title"],
                                event_author=web_event["event_author"],
                                event_publish=web_event["event_publish"],
                                events_count=events_count,
                                doc_link=web_event["doc_link"]
                            ))
                            session.commit()
                            logging.info(
                                "Добавлено новое событие для дела "
                                f"{case_number}: {web_event['event_title']} — "
                                f"{web_event['event_date']}"
                            )
                        else:
                            old_date = parse_date(db_event.event_date)
                            if new_date and (
                                not old_date or new_date > old_date
                            ):
                                db_event.event_date = web_event[
                                    "event_date"]
                                db_event.event_title = web_event[
                                    "event_title"]
                                db_event.event_author = web_event[
                                    "event_author"]
                                db_event.event_publish = web_event[
                                    "event_publish"]
                                db_event.events_count = events_count
                                db_event.doc_link = web_event["doc_link"]
                                session.commit()
                                logging.info(
                                    "Обновлено событие для дела "
                                    f"{case_number}: "
                                    f"{web_event['event_title']} — "
                                    f"{web_event['event_date']}"
                                )
                                notify_case_update(case_number, web_event)
                            else:
                                logging.info(
                                    f"Без изменений для дела {case_number}"
                                )
                        processed_cases += 1
                        save_progress(case_number, index,
                                      "parser_progress.json")
                        pbar.update(1)
                    except Exception as e:
                        logging.error(
                            f"Ошибка обработки дела {case_number}: {e}")
                        pbar.update(1)
                        continue
                if i + batch_size < len(cases):
                    logging.info(
                        f"Пауза {pause_between_batches} секунд перед "
                        f"следующим пакетом"
                    )
                    time.sleep(pause_between_batches)
        logging.info(
            f"Завершена обработка {processed_cases} из {len(cases)} дел"
        )
        clear_progress("parser_progress.json")
    except KeyboardInterrupt:
        logging.info("Процесс прерван пользователем")
    except Exception as e:
        logging.error(f"Ошибка в sync_chronology: {e}")
    finally:
        if driver:
            driver.quit()
            logging.info("Chrome драйвер закрыт")
        session.close()
        logging.info("Сессия базы данных закрыта")


def notify_case_update(case_number: str, event_data: Dict[str, Any]) -> None:
    """
    Отправляет уведомление об обновлении дела в CRM.

    Args:
        case_number: Номер дела
        event_data: Данные события для уведомления
    """
    project_id = get_project_id_for_case(case_number)
    if not project_id:
        logging.warning(f"Не найден project_id для дела {case_number}")
        return
    try:
        send_case_update_comment(
            project_id=project_id,
            event_title=event_data.get("event_title", "Без названия"),
            event_date=event_data.get("event_date", "Не указана"),
            doc_link=event_data.get("doc_link")
        )
        logging.info(
            f"Комментарий успешно отправлен в CRM для дела {case_number}"
        )
    except Exception as e:
        logging.error(
            f"Ошибка отправки комментария в CRM для дела {case_number}: {e}"
        )

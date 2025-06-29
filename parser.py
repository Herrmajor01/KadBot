"""
Модуль для парсинга дел с сайта kad.arbitr.ru.
Содержит функции для работы с Chrome драйвером, парсинга событий дел
и синхронизации хронологии с базой данных.
"""
import logging
import random
import socket
import time
from datetime import datetime
from typing import Any, Dict, Optional, Tuple

try:
    import undetected_chromedriver as uc  # type: ignore
    from selenium.common.exceptions import (  # type: ignore
        NoSuchElementException, WebDriverException)
    from selenium.webdriver.common.by import By  # type: ignore
except ImportError as e:
    raise ImportError(f"Required selenium modules are missing: {e}")

from crm_notify import send_case_update_comment
from db import Session, get_project_id_for_case
from models import Cases, Chronology

logging.basicConfig(
    filename="kad_parser.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

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


def get_driver(retries: int = 3, timeout: int = 15) -> Optional[uc.Chrome]:
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
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_argument('--disable-infobars')
    options.add_argument('--lang=ru-RU')
    options.add_argument('--window-size=1280,900')
    options.add_argument(f'--user-agent={random.choice(USER_AGENTS)}')

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
            time.sleep(10)  # Пауза 10 секунд для прогрузки страницы
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


def simulate_mouse_movement(driver: uc.Chrome) -> None:
    """
    Эмулирует движение мыши для имитации человеческого поведения.

    Args:
        driver: Chrome драйвер для выполнения JavaScript
    """
    try:
        driver.execute_script("""
            function moveMouse(x, y) {
                const event = new MouseEvent('mousemove', {
                    clientX: x,
                    clientY: y,
                    bubbles: true
                });
                document.dispatchEvent(event);
            }
            moveMouse(Math.random() * 1200, Math.random() * 800);
        """)
        time.sleep(random.uniform(0.2, 0.5))
    except Exception as e:
        logging.info(f"Ошибка эмуляции движения мыши: {e}")


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
            time.sleep(random.uniform(5.0, 10.0))  # Задержка 5–10 сек
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

            # Эмуляция человеческого поведения
            for _ in range(12):  # 12 прокруток
                x, y = random.randint(50, 1200), random.randint(50, 1200)
                driver.execute_script(f"window.scrollTo({x}, {y});")
                simulate_mouse_movement(driver)
                time.sleep(random.uniform(1.0, 2.0))
            driver.execute_script("window.scrollTo(0, 0);")
            time.sleep(random.uniform(1.0, 2.0))

            # Случайный клик по вкладкам
            try:
                tabs = driver.find_elements(By.CSS_SELECTOR, ".b-tab.js-tab")
                if tabs and random.random() > 0.3:  # 70% шанс клика
                    random.choice(tabs[:2]).click()
                    time.sleep(random.uniform(2.0, 3.0))
                    logging.info(
                        f"Эмулирован клик по вкладке для дела {case_number}"
                    )
                    driver.execute_script("window.scrollTo(0, 0);")
                    time.sleep(random.uniform(1.0, 2.0))
            except Exception as e:
                logging.info(
                    f"Не удалось кликнуть по вкладке для дела "
                    f"{case_number}: {e}"
                )

            # Попытка раскрыть хронологию
            for _ in range(3):
                try:
                    collapse_btn = driver.find_element(
                        By.CSS_SELECTOR, ".b-collapse.js-collapse"
                    )
                    if collapse_btn.is_displayed():
                        collapse_btn.click()
                        time.sleep(random.uniform(2.0, 5.0))
                        logging.info(
                            f"Раскрыта хронология для дела {case_number}"
                        )
                        break
                except NoSuchElementException:
                    logging.info(
                        f"Кнопка раскрытия хронологии не найдена для дела "
                        f"{case_number}"
                    )
                    break
                except Exception as e:
                    logging.warning(
                        f"Ошибка при клике на хронологию для дела "
                        f"{case_number}: {e}"
                    )
                    time.sleep(1.0)

            # Ожидание элементов хронологии
            for _ in range(40):  # 20 секунд
                elements = driver.find_elements(
                    By.CSS_SELECTOR, ".b-chrono-item.js-chrono-item"
                )
                if elements:
                    break
                time.sleep(0.5)
            else:
                logging.warning(
                    f"Элементы хронологии не найдены для дела {case_number} "
                    f"после 20 секунд"
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
            with open(
                f"error_{case_number.replace('/', '_')}.html",
                "w",
                encoding="utf-8"
            ) as f:
                f.write(driver.page_source)
            if attempt < 2:
                driver.refresh()
                time.sleep(random.uniform(5.0, 7.0))
            else:
                logging.error(
                    f"Не удалось получить события для дела {case_number} "
                    f"после 3 попыток"
                )
                return None, 0
    return None, 0


def sync_chronology(
    batch_size: int = 50,
    pause_between_batches: int = 120
) -> None:
    """
    Синхронизирует хронологию дел с сайта kad.arbitr.ru с базой данных.

    Обрабатывает дела пакетами, получает последние события и обновляет
    базу данных. При обнаружении новых событий отправляет уведомления в CRM.

    Args:
        batch_size: Размер пакета дел для обработки
        pause_between_batches: Пауза между пакетами в секундах
    """
    session = Session()
    driver = get_driver()
    processed_cases = 0
    try:
        cases = session.query(Cases).all()
        logging.info(f"Начата обработка {len(cases)} дел")
        for i in range(0, len(cases), batch_size):
            batch = cases[i:i + batch_size]
            logging.info(
                f"Обработка пакета дел {i+1}-"
                f"{min(i+batch_size, len(cases))} из {len(cases)}"
            )
            for case in batch:
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
                            f"Добавлено новое событие для дела {case_number}: "
                            f"{web_event['event_title']} — "
                            f"{web_event['event_date']}"
                        )
                    else:
                        old_date = parse_date(db_event.event_date)
                        if new_date and (not old_date or new_date > old_date):
                            db_event.event_date = web_event["event_date"]
                            db_event.event_title = web_event["event_title"]
                            db_event.event_author = web_event["event_author"]
                            db_event.event_publish = web_event["event_publish"]
                            db_event.events_count = events_count
                            db_event.doc_link = web_event["doc_link"]
                            session.commit()
                            logging.info(
                                f"Обновлено событие для дела {case_number}: "
                                f"{web_event['event_title']} — "
                                f"{web_event['event_date']}"
                            )
                            notify_case_update(case_number, web_event)
                        else:
                            logging.info(
                                f"Без изменений для дела {case_number}"
                            )
                    processed_cases += 1
                except Exception as e:
                    logging.error(f"Ошибка обработки дела {case_number}: {e}")
                    continue
            if i + batch_size < len(cases):
                logging.info(
                    f"Пауза {pause_between_batches} секунд перед "
                    f"следующим пакетом"
                )
                # Пауза 2 минуты без закрытия окна
                time.sleep(pause_between_batches)
        logging.info(
            f"Завершена обработка {processed_cases} из {len(cases)} дел"
        )
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

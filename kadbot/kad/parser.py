"""
Модуль для парсинга дел с сайта kad.arbitr.ru.
Содержит функции для парсинга событий дел
 и синхронизации хронологии с базой данных.
"""

import logging
import random
import re
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
    from selenium.webdriver.support import (
        expected_conditions as EC,  # type: ignore
    )
    from selenium.webdriver.support.ui import WebDriverWait  # type: ignore
    from tqdm import tqdm  # type: ignore
except ImportError as e:
    raise ImportError(f"Required modules are missing: {e}")

from kadbot.crm.calendar import create_project_calendar_event
from kadbot.crm.notify import send_case_update_comment
from kadbot.db.session import Session, get_project_id_for_case
from kadbot.db.models import Cases, Chronology
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
    driver: uc.Chrome, case_number: str
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
                    encoding="utf-8",
                ) as f:
                    f.write(driver.page_source)
                return None, 0

            # Проверка на ограничение подписки
            if "Вы можете оформить подписку на 40 дел" in driver.page_source:
                logging.warning(
                    f"Доступ к хронологии ограничен из-за подписки для дела "
                    f"{case_number}"
                )
                with open(
                    f"error_{case_number.replace('/', '_')}.html",
                    "w",
                    encoding="utf-8",
                ) as f:
                    f.write(driver.page_source)
                return None, 0

            # Эмуляция человеческого поведения (уменьшено до 3 прокруток)
            driver.execute_script("window.scrollTo(0, 0);")
            time.sleep(random.uniform(0.5, 1.0))

            # Извлекаем блок "Следующее заседание" по HTML-структуре
            hearing_date = ""
            hearing_time = ""
            hearing_room = ""
            try:
                # Ищем div с классом b-instanceAdditional, который содержит
                # информацию о заседании
                hearing_blocks = driver.find_elements(
                    By.CSS_SELECTOR, "div.b-instanceAdditional"
                )

                for block in hearing_blocks:
                    # Проверяем, содержит ли блок иконку календаря
                    calendar_icons = block.find_elements(
                        By.CSS_SELECTOR, "i.b-icons16.redCalendar"
                    )

                    if calendar_icons:
                        # Нашли блок с информацией о заседании
                        text_content = block.text.strip()
                        logging.info(
                            f"Найден блок заседания для {case_number}: "
                            f"{text_content}"
                        )

                        # Ищем дату и время в формате DD.MM.YYYY, HH:MM
                        date_time_match = re.search(
                            r"(\d{2}\.\d{2}\.\d{4}),\s*(\d{2}:\d{2})",
                            text_content
                        )

                        if date_time_match:
                            hearing_date = date_time_match.group(1)
                            hearing_time = date_time_match.group(2)

                            # Ищем номер кабинета/зала
                            room_match = re.search(r"к\.(\d+)", text_content)
                            if room_match:
                                hearing_room = room_match.group(1)
                            else:
                                # Ищем другие варианты обозначения зала
                                room_match = re.search(
                                    r"Зал[^№]*№\s*(\d+)",
                                    text_content
                                )
                                if room_match:
                                    hearing_room = room_match.group(1)
                                else:
                                    hearing_room = ""

                            logging.info(
                                "Найдено следующее заседание: %s %s %s",
                                hearing_date,
                                hearing_time,
                                hearing_room,
                            )
                            break

                # Если не нашли по структуре, пробуем резервный поиск по тексту
                if not hearing_date or not hearing_time:
                    logging.info(
                        f"Резервный поиск по тексту для дела {case_number}"
                    )
                    elems = driver.find_elements(
                        By.XPATH,
                        "//*[contains(text(),'Следующее заседание')]",
                    )
                    if elems:
                        text_source = elems[0].text.strip()
                        m = re.search(
                            (
                                r"Следующее заседание:\s*(\d{2}\.\d{2}\.\d{4}),"
                                r"\s*(\d{2}:\d{2})(?:\s*,\s*к\.(\d+))?"
                            ),
                            text_source,
                        )
                        if m:
                            hearing_date = m.group(1)
                            hearing_time = m.group(2)
                            hearing_room = m.group(3) if m.group(3) else ""
                            logging.info(
                                "Найдено следующее заседание (резервный поиск): "
                                "%s %s %s",
                                hearing_date,
                                hearing_time,
                                hearing_room,
                            )
            except Exception as e:
                logging.info(
                    "Не удалось извлечь 'Следующее заседание' для %s: %s",
                    case_number,
                    e,
                )

            # Переключение на вкладку "Судебные акты"
            try:
                tabs = WebDriverWait(driver, 8).until(
                    EC.presence_of_all_elements_located(
                        (By.CSS_SELECTOR, ".b-tab.js-tab")
                    )
                )
                for tab in tabs:
                    if "Судебные акты" in tab.text:
                        driver.execute_script("arguments[0].click();", tab)
                        time.sleep(random.uniform(1.0, 2.0))
                        logging.info(
                            f"Переключено на вкладку 'Судебные акты' для дела "
                            f"{case_number}"
                        )
                        break
            except Exception as e:
                logging.info(
                    f"Не удалось переключиться на вкладку 'Судебные акты' "
                    f"для дела {case_number}: {e}"
                )

            # Ожидание и клик по кнопке раскрытия хронологии
            try:
                collapse_btn = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable(
                        (By.CSS_SELECTOR, ".b-collapse.js-collapse")
                    )
                )
                driver.execute_script(
                    "arguments[0].scrollIntoView(true);", collapse_btn
                )
                driver.execute_script("arguments[0].click();", collapse_btn)
                time.sleep(random.uniform(1.0, 2.0))
                logging.info(f"Раскрыта хронология для дела {case_number}")
            except TimeoutException:
                logging.warning(
                    f"Кнопка раскрытия хронологии (.b-collapse.js-collapse) "
                    f"не найдена для дела {case_number} после 10 секунд"
                )
                with open(
                    f"error_{case_number.replace('/', '_')}.html",
                    "w",
                    encoding="utf-8",
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
                    encoding="utf-8",
                ) as f:
                    f.write(driver.page_source)
                return None, 0

            # Ожидание элементов хронологии
            try:
                elements = WebDriverWait(driver, 20).until(
                    EC.presence_of_all_elements_located(
                        (By.CSS_SELECTOR, ".b-chrono-item.js-chrono-item")
                    )
                )
            except TimeoutException:
                logging.warning(
                    f"Элементы хронологии (.b-chrono-item.js-chrono-item) "
                    f"не найдены для дела {case_number} после 20 секунд"
                )
                with open(
                    f"error_{case_number.replace('/', '_')}.html",
                    "w",
                    encoding="utf-8",
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
                "event_publish": safe_sel(last_event, ".b-case-publish_info")
                .replace("Дата публикации:", "")
                .strip(),
                "events_count": events_count,
                "doc_link": doc_link,
                "hearing_date": hearing_date,
                "hearing_time": hearing_time,
                "hearing_room": hearing_room,
            }
            logging.info(
                f"Спарсено событие для дела {case_number}: "
                f"{event_data['event_title']} — {event_data['event_date']}"
            )
            return event_data, events_count

        except Exception as e:
            logging.error(
                f"Ошибка при парсинге дела {case_number} (попытка {attempt + 1}): {e}"
            )
            if attempt < 2:
                time.sleep(random.uniform(2.0, 5.0))
                continue
            else:
                logging.error(
                    f"Не удалось спарсить дело {case_number} после 3 попыток"
                )
                return None, 0

    return None, 0


def sync_chronology(
    start_index: int = 0,
    batch_size: int = 10,
    pause_between_batches: int = 5,
) -> None:
    """
    Синхронизирует хронологию дел с сайта kad.arbitr.ru.

    Args:
        start_index: Начальный индекс для обработки
        batch_size: Размер пакета для обработки
        pause_between_batches: Пауза между пакетами в секундах
    """
    session = Session()
    driver = None
    processed_cases = 0

    try:
        # Загружаем прогресс
        progress = load_progress("parser_progress.json")
        if progress:
            start_index = progress.get("last_index", start_index)
            logging.info(f"Восстановлен прогресс с индекса {start_index}")

        # Получаем список только активных дел
        try:
            cases = session.query(Cases).filter(Cases.is_active == True).all()  # noqa: E712
        except Exception:
            # На случай отсутствия колонки (старые БД) — fallback на все дела
            cases = session.query(Cases).all()
        if not cases:
            logging.warning("Не найдено дел для обработки")
            return

        logging.info(f"Найдено {len(cases)} дел для обработки")
        if start_index >= len(cases):
            logging.info("Все дела уже обработаны")
            return

        # Инициализируем драйвер
        driver = get_driver()
        if not driver:
            logging.error("Не удалось инициализировать Chrome драйвер")
            return

        with tqdm(total=len(cases), desc="Обработка дел", unit="дело") as pbar:
            for i in range(0, len(cases), batch_size):
                batch = cases[i: i + batch_size]
                logging.info(
                    f"Обработка пакета дел {i+1+start_index}-"
                    f"{min(i+batch_size+start_index, len(cases)+start_index)} "
                    f"из {len(cases)+start_index}"
                )
                for index, case in enumerate(batch, start=i + start_index):
                    case_number = case.case_number
                    try:
                        db_event = (
                            session.query(Chronology)
                            .filter_by(case_number=case_number)
                            .order_by(Chronology.id.desc())
                            .first()
                        )
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
                            # Новое событие - добавляем в БД
                            new_chronology = Chronology(
                                case_number=case_number,
                                event_date=web_event["event_date"],
                                event_title=web_event["event_title"],
                                event_author=web_event["event_author"],
                                event_publish=web_event["event_publish"],
                                events_count=events_count,
                                doc_link=web_event["doc_link"],
                                hearing_date=web_event.get("hearing_date"),
                                hearing_time=web_event.get("hearing_time"),
                                hearing_room=web_event.get("hearing_room"),
                                hearing_created_at=None,
                            )
                            session.add(new_chronology)
                            session.commit()

                            # Получаем ID добавленной записи
                            db_event = new_chronology

                            logging.info(
                                "Добавлено новое событие для дела "
                                f"{case_number}: {web_event['event_title']} — "
                                f"{web_event['event_date']}"
                            )

                            # Если есть информация о заседании, создаём событие в календаре
                            if (web_event.get("hearing_date") and
                                    web_event.get("hearing_time")):
                                notify_case_update(
                                    case_number, web_event, db_event.id)
                        else:
                            old_date = parse_date(db_event.event_date)
                            hearing_changed = (
                                db_event.hearing_date != web_event.get("hearing_date") or
                                db_event.hearing_time != web_event.get("hearing_time") or
                                db_event.hearing_room != web_event.get(
                                    "hearing_room")
                            )
                            has_newer_event = bool(new_date and (
                                not old_date or new_date > old_date))
                            if has_newer_event or hearing_changed:
                                # Обновляем основную информацию (держим БД в актуальном состоянии)
                                db_event.event_date = web_event["event_date"]
                                db_event.event_title = web_event["event_title"]
                                db_event.event_author = web_event["event_author"]
                                db_event.event_publish = web_event["event_publish"]
                                db_event.events_count = events_count
                                db_event.doc_link = web_event["doc_link"]

                                # Обновляем информацию о заседании
                                db_event.hearing_date = web_event.get(
                                    "hearing_date")
                                db_event.hearing_time = web_event.get(
                                    "hearing_time")
                                db_event.hearing_room = web_event.get(
                                    "hearing_room")

                                # Если изменилась информация о заседании, сбрасываем флаг создания
                                if hearing_changed:
                                    db_event.hearing_created_at = None

                                session.commit()

                                logging.info(
                                    "Обновлено событие для дела "
                                    f"{case_number}: "
                                    f"{web_event['event_title']} — "
                                    f"{web_event['event_date']}"
                                )

                                if hearing_changed:
                                    logging.info(
                                        "Обнаружены изменения в информации о заседании "
                                        f"для дела {case_number}"
                                    )

                                # Отправляем уведомление и создаём событие в календаре
                                notify_case_update(
                                    case_number, web_event, db_event.id)
                            else:
                                logging.info(
                                    f"Без изменений для дела {case_number}")
                        processed_cases += 1
                        save_progress(
                            case_number, index, "parser_progress.json"
                        )
                        pbar.update(1)
                    except Exception as e:
                        logging.error(
                            f"Ошибка обработки дела {case_number}: {e}"
                        )
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


def notify_case_update(
    case_number: str,
    event_data: Dict[str, Any],
    chronology_id: int
) -> None:
    """
    Отправляет уведомление об обновлении дела в CRM и создаёт событие в календаре.

    Args:
        case_number: Номер дела
        event_data: Данные события для уведомления
        chronology_id: ID записи в таблице Chronology
    """
    project_id = get_project_id_for_case(case_number)
    if not project_id:
        logging.warning(f"Не найден project_id для дела {case_number}")
        return

    try:
        # Отправляем комментарий в CRM
        send_case_update_comment(
            project_id=project_id,
            event_title=event_data.get("event_title", "Без названия"),
            event_date=event_data.get("event_date", "Не указана"),
            doc_link=event_data.get("doc_link"),
        )
        logging.info(
            f"Комментарий успешно отправлен в CRM для дела {case_number}"
        )

        # Проверяем, нужно ли создать событие в календаре
        hearing_date = event_data.get("hearing_date")
        hearing_time = event_data.get("hearing_time")

        if hearing_date and hearing_time:
            # Проверяем, не было ли уже создано событие для этого заседания
            session = Session()
            try:
                db_event = session.get(Chronology, chronology_id)
                if db_event and db_event.hearing_created_at:
                    logging.info(
                        f"Событие в календаре уже создано для дела {case_number} "
                        f"в {db_event.hearing_created_at}"
                    )
                    return
            finally:
                session.close()

            try:
                logging.info(
                    "Найдена информация о заседании для дела %s: "
                    "дата=%s, время=%s, кабинет=%s",
                    case_number,
                    hearing_date,
                    hearing_time,
                    event_data.get("hearing_room") or "не указан",
                )

                # Парсим дату и время
                date_obj = datetime.strptime(hearing_date, "%d.%m.%Y")
                time_obj = datetime.strptime(hearing_time, "%H:%M").time()
                hearing_datetime = datetime.combine(date_obj.date(), time_obj)

                logging.info(
                    "Создаю событие календаря для дела %s на %s",
                    case_number,
                    hearing_datetime.strftime("%d.%m.%Y %H:%M"),
                )

                # Создаём событие в календаре CRM (ID определяется автоматически)
                calendar_result = create_project_calendar_event(
                    project_id=project_id,
                    case_number=case_number,
                    start_dt=hearing_datetime,
                    duration_minutes=60,
                    room=event_data.get("hearing_room"),
                )

                if calendar_result:
                    # Обновляем флаг создания события в БД
                    session = Session()
                    try:
                        db_event = session.get(Chronology, chronology_id)
                        if db_event:
                            db_event.hearing_created_at = datetime.now().strftime(
                                "%Y-%m-%d %H:%M:%S"
                            )
                            try:
                                event_id = (
                                    calendar_result.get("response", {}).get("id")
                                    if isinstance(calendar_result, dict)
                                    else None
                                )
                                if event_id:
                                    db_event.hearing_event_id = str(event_id)
                            except Exception:
                                pass
                            session.commit()
                            logging.info(
                                "Обновлён флаг создания события в календаре "
                                f"для дела {case_number}"
                            )
                    finally:
                        session.close()

                    logging.info(
                        "Событие календаря успешно создано для дела %s. "
                        "Результат: %s",
                        case_number,
                        calendar_result,
                    )
                else:
                    logging.warning(
                        "Не удалось создать событие календаря для дела %s",
                        case_number,
                    )

            except Exception as e:
                logging.error(
                    "Ошибка при создании события календаря для дела %s: %s",
                    case_number,
                    str(e),
                    exc_info=True,
                )
        else:
            logging.info(
                "Информация о следующем заседании для дела %s не найдена",
                case_number,
            )

    except Exception as e:
        logging.error(
            f"Ошибка отправки комментария в CRM для дела {case_number}: {e}"
        )


if __name__ == "__main__":
    sync_chronology()

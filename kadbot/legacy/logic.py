"""
Легаси-модуль с основной логикой парсинга и обработки дел.
Сохранён для совместимости, не используется в текущем коде.
"""

import logging
import random
import time
from datetime import datetime
from parser import get_case_events, get_driver  # type: ignore
from typing import Any, Dict, Optional

from crm_notify import send_case_update_comment
from db import Session, get_project_id_for_case
from models import Cases, Chronology

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


def get_last_event_from_db(session, case_number: str) -> Optional[Chronology]:
    """
    Получает последнее событие для дела из базы данных.

    Args:
        session: Сессия базы данных
        case_number: Номер дела

    Returns:
        Chronology: Последнее событие или None, если событий нет
    """
    return (
        session.query(Chronology)
        .filter_by(case_number=case_number)
        .order_by(Chronology.id.desc())
        .first()
    )


def save_event_to_db(
    session, case_number: str, event_data: Dict[str, Any], events_count: int
) -> None:
    """
    Сохраняет новое событие в базу данных.

    Args:
        session: Сессия базы данных
        case_number: Номер дела
        event_data: Данные события
        events_count: Общее количество событий
    """
    chronology = Chronology(
        case_number=case_number,
        event_title=event_data.get("event_title", ""),
        event_date=event_data.get("event_date", ""),
        event_author=event_data.get("event_author", ""),
        event_publish=event_data.get("event_publish", ""),
        doc_link=event_data.get("doc_link", ""),
        events_count=events_count,
    )
    session.add(chronology)
    session.commit()
    logging.info(
        f"Добавлено новое событие для дела {case_number}: "
        f"{event_data['event_title']} — {event_data['event_date']}"
    )


def update_event_in_db(
    session,
    chronology: Chronology,
    event_data: Dict[str, Any],
    events_count: int,
) -> None:
    """
    Обновляет существующее событие в базе данных.

    Args:
        session: Сессия базы данных
        chronology: Объект события для обновления
        event_data: Новые данные события
        events_count: Общее количество событий
    """
    chronology.event_title = event_data.get("event_title", "")
    chronology.event_date = event_data.get("event_date", "")
    chronology.event_author = event_data.get("event_author", "")
    chronology.event_publish = event_data.get("event_publish", "")
    chronology.doc_link = event_data.get("doc_link", "")
    chronology.events_count = events_count
    session.commit()
    logging.info(
        f"Обновлено событие для дела {chronology.case_number}: "
        f"{event_data['event_title']} — {event_data['event_date']}"
    )


def parse_and_save_case(session, driver, case_number: str) -> None:
    """
    Парсит и сохраняет события для конкретного дела.

    Args:
        session: Сессия базы данных
        driver: Chrome драйвер для парсинга
        case_number: Номер дела
    """
    try:
        event_data, events_count = get_case_events(driver, case_number)
        if not event_data:
            logging.warning(f"Дело {case_number}: событий не найдено")
            return

        db_event = get_last_event_from_db(session, case_number)
        new_date = parse_date(event_data["event_date"])

        if not db_event:
            save_event_to_db(session, case_number, event_data, events_count)
            notify_case_update(case_number, event_data)
        else:
            old_date = parse_date(db_event.event_date)
            if new_date and (not old_date or new_date > old_date):
                update_event_in_db(session, db_event, event_data, events_count)
                notify_case_update(case_number, event_data)
            else:
                logging.info(f"Без изменений для дела {case_number}")
    except Exception as e:
        logging.error(f"Ошибка обработки дела {case_number}: {e}")


def parse_all_cases() -> None:
    """
    Парсит все дела из базы данных.

    Обрабатывает все дела последовательно, получая последние события
    и обновляя базу данных при необходимости.
    """
    session = Session()
    driver = get_driver()
    try:
        all_cases = session.query(Cases).all()
        total = len(all_cases)
        logging.info(f"Начата обработка {total} дел")
        for idx, case in enumerate(all_cases, 1):
            logging.info(f"[{idx}/{total}] Проверка {case.case_number}")
            parse_and_save_case(session, driver, case.case_number)
            time.sleep(random.uniform(0.7, 1.3))
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
    send_case_update_comment(
        project_id=project_id,
        event_title=event_data.get("event_title", "Без названия"),
        event_date=event_data.get("event_date", "Не указана"),
        doc_link=event_data.get("doc_link"),
    )

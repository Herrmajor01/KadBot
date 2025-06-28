from db import Session
from models import Chronology
from parser import get_driver, get_case_events


def get_last_event_from_db(session, case_number):
    return session.query(Chronology).filter_by(case_number=case_number).order_by(Chronology.event_date.desc()).first()


def save_event_to_db(session, case_number, event_data, events_count):
    chronology = Chronology(
        case_number=case_number,
        event_title=event_data.get("event_title", ""),
        event_date=event_data.get("event_date", ""),
        event_author=event_data.get("event_author", ""),
        event_publish=event_data.get("event_publish", ""),
        doc_link=event_data.get("doc_link", ""),
        events_count=events_count
    )
    session.add(chronology)
    session.commit()


def update_event_in_db(session, chronology, event_data, events_count):
    chronology.event_title = event_data.get("event_title", "")
    chronology.event_date = event_data.get("event_date", "")
    chronology.event_author = event_data.get("event_author", "")
    chronology.event_publish = event_data.get("event_publish", "")
    chronology.doc_link = event_data.get("doc_link", "")
    chronology.events_count = events_count
    session.commit()


def parse_and_save_case(session, driver, case_number):
    event_data, events_count = get_case_events(driver, case_number)
    if not event_data:
        print(f"Дело {case_number}: событий не найдено")
        return

    db_event = get_last_event_from_db(session, case_number)
    if not db_event:
        save_event_to_db(session, case_number, event_data, events_count)
        print(
            f"[НОВОЕ] {case_number}: {event_data['event_title']} | {event_data['event_date']}")
    else:
        if (
            event_data['event_title'] != db_event.event_title or
            event_data['event_date'] != db_event.event_date
        ):
            update_event_in_db(session, db_event, event_data, events_count)
            print(
                f"[ОБНОВЛЕНО] {case_number}: {event_data['event_title']} | {event_data['event_date']}")
        else:
            print(f"[БЕЗ ИЗМЕНЕНИЙ] {case_number}")


def parse_all_cases():
    from models import Case  # если есть отдельная таблица Case с case_number
    session = Session()
    all_cases = session.query(Case).all()
    total = len(all_cases)
    driver = get_driver()
    try:
        for idx, case in enumerate(all_cases, 1):
            print(f"[{idx}/{total}] Проверка {case.case_number} ...")
            parse_and_save_case(session, driver, case.case_number)
            import time
            import random
            time.sleep(random.uniform(0.7, 1.3))
    finally:
        driver.quit()
        session.close()

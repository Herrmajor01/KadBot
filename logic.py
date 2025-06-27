from db import get_case_numbers, get_last_event, save_event
from parser import get_case_events, get_driver
import time


def main_process_cases():
    """
    Основная обработка всех дел:
    драйвер создаётся один раз и передаётся далее.
    """
    driver = get_driver()
    try:
        case_numbers = get_case_numbers()
        for case_number in case_numbers:
            print(f"Обработка дела {case_number} ...")
            event_data, events_count = get_case_events(driver, case_number)
            if event_data:
                last_event = get_last_event(case_number)
                if not last_event or last_event['event_date'] != event_data['event_date']:
                    save_event(
                        case_number,
                        event_data['event_date'],
                        event_data['event_title'],
                        event_data['event_author'],
                        event_data['event_publish'],
                        events_count,
                        event_data['doc_link'],
                    )
                    print(
                        f"Сохранено новое событие по делу {case_number}: "
                        f"{event_data['event_date']}, "
                        f"{event_data['event_title']} ({events_count} событий)"
                    )
                else:
                    print(f"Нет новых событий по делу {case_number}")
            else:
                print(f"Нет событий по делу {case_number}")
            time.sleep(1)
    finally:
        driver.quit()

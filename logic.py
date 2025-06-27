from db import get_case_numbers, get_last_event, save_event
from parser import get_driver, load_case_page, parse_last_event_and_count


def process_case(driver, case_number):
    """
    Обрабатывает одно дело: обновляет событие, если есть новое.
    """
    load_case_page(driver, case_number)
    event_data, events_count = parse_last_event_and_count(driver)
    if not event_data:
        print(f"Нет событий по делу {case_number}")
        return
    db_event = get_last_event(case_number)
    # Если нет события в базе, либо событие изменилось — сохраняем
    if (not db_event or event_data[0] != db_event[0] or
            event_data[1] != db_event[1]):
        save_event(case_number, *event_data, events_count)
        print(f"Сохранено новое событие по делу {case_number}: "
              f"{event_data[0]}, {event_data[1]} ({events_count} событий)")
    else:
        print(f"Событие по делу {case_number} не изменилось.")


def main_process_cases():
    """
    Основная функция: проходит по всем делам и обновляет их события.
    """
    case_numbers = get_case_numbers()
    driver = get_driver()
    try:
        for case_number in case_numbers:
            process_case(driver, case_number)
    finally:
        driver.quit()

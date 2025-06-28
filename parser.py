import time
import random
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from db import Session
from models import Cases, Chronology


def get_driver():
    options = uc.ChromeOptions()
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_argument('--disable-infobars')
    options.add_argument('--lang=ru-RU')
    options.add_argument('--window-size=1280,900')
    return uc.Chrome(options=options, use_subprocess=True)


def get_case_events(driver, case_number):
    url = f"https://kad.arbitr.ru/Card?number={case_number}"
    driver.get(url)
    time.sleep(random.uniform(1.2, 1.7))
    for _ in range(7):
        x, y = random.randint(50, 1200), random.randint(50, 800)
        driver.execute_script(f"window.scrollTo({x}, {y});")
        time.sleep(random.uniform(0.3, 0.7))
    time.sleep(1.2)
    try:
        collapse_btn = driver.find_element(
            By.CSS_SELECTOR, ".b-collapse.js-collapse")
        if collapse_btn.is_displayed():
            collapse_btn.click()
            time.sleep(1.2)
    except Exception:
        pass
    for _ in range(25):
        elements = driver.find_elements(
            By.CSS_SELECTOR, ".b-chrono-item.js-chrono-item")
        if elements:
            break
        time.sleep(0.5)
    else:
        return None, 0
    events_count = len(elements)
    last_event = elements[0]

    def safe_sel(el, sel):
        try:
            return el.find_element(By.CSS_SELECTOR, sel).text.strip()
        except Exception:
            return ""
    doc_link = ""
    doc_links = last_event.find_elements(
        By.CSS_SELECTOR, "a.js-case-result-text--doc_link")
    if doc_links:
        doc_link = doc_links[0].get_attribute("href")
    event_data = {
        "event_date": safe_sel(last_event, ".case-date"),
        "event_title": safe_sel(last_event, ".case-type"),
        "event_author": safe_sel(last_event, ".case-subject"),
        "event_publish": safe_sel(last_event, ".b-case-publish_info"),
        "doc_link": doc_link
    }
    return event_data, events_count


def sync_chronology():
    session = Session()
    cases = session.query(Cases).all()
    driver = get_driver()
    try:
        for case in cases:
            case_number = case.case_number
            db_event = session.query(Chronology).filter_by(
                case_number=case_number).order_by(Chronology.id.desc()).first()
            web_event, events_count = get_case_events(driver, case_number)
            if not web_event:
                print(f"Не удалось получить события для дела {case_number}")
                continue
            if not db_event:
                # В базе нет событий — добавляем
                session.add(Chronology(case_number=case_number,
                                       event_date=web_event["event_date"],
                                       event_title=web_event["event_title"],
                                       event_author=web_event["event_author"],
                                       event_publish=web_event["event_publish"],
                                       events_count=events_count,
                                       doc_link=web_event["doc_link"]))
                print(f"Добавлено новое событие по делу {case_number}")
            else:
                # Сравниваем даты
                if db_event.event_date != web_event["event_date"]:
                    session.add(Chronology(case_number=case_number,
                                           event_date=web_event["event_date"],
                                           event_title=web_event["event_title"],
                                           event_author=web_event["event_author"],
                                           event_publish=web_event["event_publish"],
                                           events_count=events_count,
                                           doc_link=web_event["doc_link"]))
                    print(
                        f"Обновление: В деле {case_number} новое событие: {web_event['event_title']} — {web_event['event_date']}")
            session.commit()
    finally:
        driver.quit()
        session.close()

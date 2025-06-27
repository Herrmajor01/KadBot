"""
Парсер для получения событий по делу с сайта kad.arbitr.ru с использованием Selenium и undetected_chromedriver.
"""

import undetected_chromedriver as uc  # type: ignore
from selenium.webdriver.common.by import By  # type: ignore
import time
import random


def get_driver():
    """
    Создаёт и возвращает selenium webdriver для парсинга.
    """
    options = uc.ChromeOptions()
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_argument('--disable-infobars')
    options.add_argument('--lang=ru-RU')
    options.add_argument('--window-size=1280,900')
    return uc.Chrome(options=options, use_subprocess=True)


def get_case_events(driver, case_number):
    """
    Получает последнее событие по делу и общее количество событий.
    Возвращает (dict, int): данные события и число событий.
    """
    url = f"https://kad.arbitr.ru/Card?number={case_number}"
    driver.get(url)
    time.sleep(random.uniform(1.2, 1.7))

    # Эмулируем поведение пользователя
    for _ in range(7):
        x, y = random.randint(50, 1200), random.randint(50, 800)
        driver.execute_script(f"window.scrollTo({x}, {y});")
        time.sleep(random.uniform(0.3, 0.7))
    time.sleep(1.2)

    # Клик по "Показать полную хронологию"
    try:
        collapse_btn = driver.find_element(
            By.CSS_SELECTOR, ".b-collapse.js-collapse"
        )
        if collapse_btn.is_displayed():
            collapse_btn.click()
            time.sleep(1.2)
    except Exception:
        pass  # Кнопка может отсутствовать

    # Получаем все события
    for _ in range(25):
        elements = driver.find_elements(
            By.CSS_SELECTOR, ".b-chrono-item.js-chrono-item"
        )
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

    def safe_attr(el, sel, attr):
        try:
            return el.find_element(By.CSS_SELECTOR, sel).get_attribute(attr)
        except Exception:
            return ""

    # Берём только последнее событие (первый элемент)
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
        "event_publish": safe_sel(last_event, ".b-case-publish_info"),
        "doc_link": doc_link
    }
    return event_data, events_count

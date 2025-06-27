import time
import random
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By


def get_driver():
    """
    Создаёт и возвращает экземпляр ChromeDriver.
    """
    options = uc.ChromeOptions()
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_argument('--disable-infobars')
    options.add_argument('--lang=ru-RU')
    options.add_argument("--window-size=1280,900")
    driver = uc.Chrome(options=options, use_subprocess=True)
    return driver


def load_case_page(driver, case_number):
    """
    Загружает страницу дела и раскрывает хронологию.
    """
    url = f"https://kad.arbitr.ru/Card?number={case_number}"
    driver.get(url)
    time.sleep(random.uniform(1, 2))
    for _ in range(7):
        x, y = random.randint(50, 1200), random.randint(50, 800)
        driver.execute_script(f"window.scrollTo({x}, {y});")
        time.sleep(random.uniform(0.3, 0.7))
    time.sleep(1.2)
    try:
        btn = driver.find_element(By.CSS_SELECTOR,
                                  ".b-collapse.js-collapse")
        if btn.is_displayed():
            btn.click()
            time.sleep(1.2)
    except Exception:
        pass


def parse_last_event_and_count(driver):
    """
    Возвращает данные о самом свежем событии и общее количество событий.
    """
    for _ in range(25):
        elements = driver.find_elements(
            By.CSS_SELECTOR, ".b-chrono-item.js-chrono-item")
        if elements:
            break
        time.sleep(0.5)
    else:
        return None, 0
    events_count = len(elements)
    chrono = elements[0]
    try:
        event_date = chrono.find_element(
            By.CSS_SELECTOR, ".case-date").text.strip()
    except Exception:
        event_date = ""
    try:
        event_title = chrono.find_element(
            By.CSS_SELECTOR, ".case-type").text.strip()
    except Exception:
        event_title = ""
    try:
        event_author = chrono.find_element(
            By.CSS_SELECTOR, ".case-subject").text.strip()
    except Exception:
        event_author = ""
    try:
        event_publish = chrono.find_element(
            By.CSS_SELECTOR, ".b-case-publish_info"
        ).text.replace("Дата публикации:", "").strip()
    except Exception:
        event_publish = ""
    return (event_date, event_title,
            event_author, event_publish), events_count

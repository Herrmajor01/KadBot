import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
import time
import random


def get_driver():
    options = uc.ChromeOptions()
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_argument('--disable-infobars')
    options.add_argument('--lang=ru-RU')
    options.add_argument("--window-size=1280,900")
    return uc.Chrome(options=options, use_subprocess=True)


def parse_case_events(case_number):
    driver = get_driver()
    try:
        url = f"https://kad.arbitr.ru/Card?number={case_number}"
        driver.get(url)
        time.sleep(random.uniform(1, 2))
        # Имитируем поведение пользователя, прокрутка и т.д.
        for _ in range(7):
            x, y = random.randint(50, 1200), random.randint(50, 800)
            driver.execute_script(f"window.scrollTo({x}, {y});")
            time.sleep(random.uniform(0.3, 0.7))
        time.sleep(1.2)

        # Пытаемся раскрыть полную хронологию
        try:
            collapse_btn = driver.find_element(
                By.CSS_SELECTOR, ".b-collapse.js-collapse")
            if collapse_btn.is_displayed():
                collapse_btn.click()
                time.sleep(1.2)
        except Exception as e:
            pass  # не всегда кнопка есть

        # Собираем элементы хронологии
        items = []
        for _ in range(25):
            elements = driver.find_elements(
                By.CSS_SELECTOR, ".b-chrono-item.js-chrono-item")
            if elements:
                break
            time.sleep(0.5)
        else:
            driver.quit()
            return None, 0

        # Берём только первое (последнее по времени) событие
        latest = None
        latest_date = ""
        for el in elements:
            try:
                date_text = el.find_element(
                    By.CSS_SELECTOR, ".case-date").text.strip()
            except Exception:
                date_text = ""
            try:
                event_title = el.find_element(
                    By.CSS_SELECTOR, ".case-type").text.strip()
            except Exception:
                event_title = ""
            try:
                event_author = el.find_element(
                    By.CSS_SELECTOR, ".case-subject").text.strip()
            except Exception:
                event_author = ""
            try:
                event_publish = el.find_element(
                    By.CSS_SELECTOR, ".b-case-publish_info").text.strip()
            except Exception:
                event_publish = ""
            # TODO: обработать даты для сравнения, если нужно, тут можно взять самый свежий
            # или просто взять первый элемент из списка (обычно он самый свежий)
            if not latest:
                latest = (date_text, event_title, event_author, event_publish)
                latest_date = date_text

        driver.quit()
        return latest, len(elements)

    except Exception as ex:
        print("Ошибка парсинга:", ex)
        driver.quit()
        return None, 0

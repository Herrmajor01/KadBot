'''
Обход капчи на сайте kad.arbitr.ru с помощью undetected_chromedriver
и случайной прокрутки страницы.
'''

import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
import time
import random

options = uc.ChromeOptions()
options.add_argument('--no-sandbox')
options.add_argument('--disable-blink-features=AutomationControlled')
options.add_argument('--disable-infobars')
options.add_argument('--lang=ru-RU')
options.add_argument("--window-size=1280,900")

driver = uc.Chrome(options=options, use_subprocess=True)

driver.get("https://kad.arbitr.ru/Card?number=А55-15891/2025")
time.sleep(random.uniform(1, 2))

for _ in range(7):
    x, y = random.randint(50, 1200), random.randint(50, 800)
    driver.execute_script(f"window.scrollTo({x}, {y});")
    time.sleep(random.uniform(0.3, 0.7))
time.sleep(1.2)

try:
    header = driver.find_element(By.CLASS_NAME, "b-case-header")
    print("Успешно зашли на карточку дела!")
    print(header.text)
except Exception as e:
    print("Капча или не загрузилась карточка")
    print(driver.page_source[:2000])

driver.quit()

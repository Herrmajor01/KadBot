import os
import requests
import sqlite3
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("ASPRO_API_KEY")
COMPANY = os.getenv("ASPRO_COMPANY")
DB_PATH = "kad_cases.db"


def get_projects():
    """
    Получить все проекты из CRM по API Aspro.

    Возвращает список словарей с проектами.
    """
    url = (
        f"https://{COMPANY}.aspro.cloud/api/v1/module/st/projects/list"
    )
    params = {"api_key": API_KEY}
    projects = []
    page = 1
    while True:
        params["page"] = page
        resp = requests.get(url, params=params, timeout=10)
        data = resp.json()
        if "error" in data:
            print("Ошибка ответа:", data)
            break
        items = data.get("response", {}).get("items", [])
        if not items:
            break
        projects.extend(items)
        total = data.get("response", {}).get("total", 0)
        if len(projects) >= total:
            break
        page += 1
    return projects


def extract_case_number(name):
    """
    Извлекает номер дела из названия проекта (А60-12345/2023).

    Возвращает None, если номер не найден.
    """
    import re
    match = re.search(r"[АA]\d{2,}-\d+/\d{4}", name)
    if match:
        return match.group(0)
    return None


def add_case_to_db(case_number):
    """
    Добавляет номер дела в таблицу cases, если такого ещё нет.
    """
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(
        "INSERT OR IGNORE INTO cases (case_number) VALUES (?)",
        (case_number,),
    )
    conn.commit()
    conn.close()


def sync_crm_projects_to_db():
    """
    Синхронизирует проекты из CRM с базой: добавляет новые номера дел.
    """
    projects = get_projects()
    count = 0
    for proj in projects:
        name = proj.get("name", "")
        case_number = extract_case_number(name)
        if not case_number:
            print(f"Не найден номер в проекте: {name}")
            continue
        add_case_to_db(case_number)
        print(f"Добавлено дело: {case_number}")
        count += 1
    print(f"Итого добавлено {count} дел")


if __name__ == "__main__":
    sync_crm_projects_to_db()

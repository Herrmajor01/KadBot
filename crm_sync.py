"""
Модуль для синхронизации списка дел из CRM с локальной базой данных.
"""

import os
import requests  # type: ignore
import sqlite3

DB_PATH = "kad_cases.db"
API_KEY = os.getenv("ASPRO_API_KEY")
COMPANY = os.getenv("ASPRO_COMPANY")
PROJECTS_URL = (
    f"https://{COMPANY}.aspro.cloud/api/v1/module/st/projects/list"
)
PAGE_SIZE = 50


def get_crm_projects():
    """
    Получить список неархивных проектов (дел) из CRM.
    """
    headers = {"Authorization": f"Bearer {API_KEY}"}
    projects = []
    page = 1
    while True:
        params = {
            "page": page,
            "perPage": PAGE_SIZE,
            "archive": 0,
        }
        resp = requests.get(PROJECTS_URL, headers=headers,
                            params=params, timeout=15)
        data = resp.json()
        if not data.get("data"):
            break
        projects.extend(data["data"])
        if len(data["data"]) < PAGE_SIZE:
            break
        page += 1
    return projects


def get_case_numbers_from_db():
    """
    Получить список номеров дел, сохранённых в базе.
    """
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.execute("SELECT case_number FROM cases")
        return set(row[0] for row in cur.fetchall())


def add_case_to_db(case_number):
    """
    Добавить дело в базу, если его ещё нет.
    """
    with sqlite3.connect(DB_PATH) as conn:
        try:
            conn.execute(
                "INSERT INTO cases (case_number) VALUES (?)",
                (case_number,)
            )
        except sqlite3.IntegrityError:
            pass  # Уже есть


def delete_case_from_db(case_number):
    """
    Удалить дело из базы.
    """
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            "DELETE FROM cases WHERE case_number = ?",
            (case_number,)
        )


def sync_cases_with_crm():
    """
    Синхронизировать список дел из CRM с базой.

    Добавлять новые, удалять архивные.
    """
    print("Получаем список проектов из CRM...")
    crm_projects = get_crm_projects()
    crm_case_numbers = set()

    for prj in crm_projects:
        # Здесь предположим, что номер дела хранится в поле "number"
        number = prj.get("number") or ""
        number = number.strip()
        if number:
            crm_case_numbers.add(number)
            add_case_to_db(number)

    db_case_numbers = get_case_numbers_from_db()

    # Удаление дел, которых нет в CRM
    for old_case in db_case_numbers - crm_case_numbers:
        delete_case_from_db(old_case)
        print(f"Дело № {old_case} удалено из базы (оно в архиве CRM).")

    print(
        f"Итого: {len(
            crm_case_numbers)} активных дел в базе синхронизировано с CRM."
    )


if __name__ == "__main__":
    sync_cases_with_crm()

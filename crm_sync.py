import os
import requests
import re
from dotenv import load_dotenv
from db import Session
from models import Cases

load_dotenv()
API_KEY = os.getenv("ASPRO_API_KEY")
COMPANY = os.getenv("ASPRO_COMPANY")


def get_projects():
    url = f"https://{COMPANY}.aspro.cloud/api/v1/module/st/projects/list"
    params = {"api_key": API_KEY}
    projects = []
    page = 1
    while True:
        params["page"] = page
        resp = requests.get(url, params=params, timeout=15)
        data = resp.json()
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
    match = re.search(r"[АA]\d{2,}-\d+/\d{4}", name)
    if match:
        return match.group(0)
    return None


def sync_crm_projects_to_db():
    session = Session()
    all_projects = get_projects()
    # Только неархивные
    active_projects = [p for p in all_projects if p.get("is_archive", 0) == 0]
    print(f"Всего проектов в CRM: {len(all_projects)}")
    print(f"Новых, неархивных проектов: {len(active_projects)}")

    db_case_numbers = {c.case_number for c in session.query(Cases).all()}

    active_case_numbers = set()
    added = 0

    for proj in active_projects:
        name = proj.get("name", "")
        case_number = extract_case_number(name)
        if not case_number:
            continue
        active_case_numbers.add(case_number)
        if case_number not in db_case_numbers:
            session.add(Cases(case_number=case_number))
            print(f"Добавлено дело: {case_number}")
            added += 1

    # Удаляем из БД те, которых больше нет среди неархивных
    for case_number in db_case_numbers:
        if case_number not in active_case_numbers:
            obj = session.query(Cases).filter_by(
                case_number=case_number).first()
            if obj:
                session.delete(obj)
                print(f"Удалено архивное дело: {case_number}")

    session.commit()
    session.close()
    print(f"Итого добавлено: {added}")

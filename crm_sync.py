"""
Модуль для синхронизации проектов из Aspro CRM с базой данных.
Извлекает номера дел из названий проектов и обновляет базу данных.
"""
import logging
import os
import re
from typing import Any, Dict, List, Optional

import requests  # type: ignore
from dotenv import load_dotenv  # type: ignore

from db import Session
from models import Cases

logging.basicConfig(
    filename="kad_parser.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

load_dotenv()
API_KEY = os.getenv("ASPRO_API_KEY")
COMPANY = os.getenv("ASPRO_COMPANY")


def get_projects() -> List[Dict[str, Any]]:
    """
    Получает список всех проектов из Aspro CRM через API.

    Returns:
        List[Dict]: Список проектов с их данными
    """
    url = f"https://{COMPANY}.aspro.cloud/api/v1/module/st/projects/list"
    params = {"api_key": API_KEY}
    projects = []
    page = 1

    while True:
        params["page"] = str(page)
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


def extract_case_number(name: str) -> Optional[str]:
    """
    Извлекает номер дела из названия проекта.

    Args:
        name: Название проекта

    Returns:
        str: Номер дела или None, если не найден
    """
    match = re.search(r"[АA]\d{2,}-\d+/\d{4}", name)
    if match:
        return match.group(0)
    return None


def sync_crm_projects_to_db() -> None:
    """
    Синхронизирует проекты из CRM с базой данных.

    Получает все проекты из CRM, извлекает номера дел из названий,
    добавляет новые дела в базу данных и удаляет архивные.
    """
    session = Session()
    try:
        all_projects = get_projects()
        active_projects = [
            p for p in all_projects if p.get("is_archive", 0) == 0
        ]
        logging.info(f"Всего проектов в CRM: {len(all_projects)}")
        logging.info(f"Новых, неархивных проектов: {len(active_projects)}")

        db_case_numbers = {c.case_number for c in session.query(Cases).all()}
        active_case_numbers = set()
        added = 0

        for proj in active_projects:
            name = proj.get("name", "")
            case_number = extract_case_number(name)
            if not case_number:
                continue
            project_id = proj.get("id")
            active_case_numbers.add(case_number)
            if case_number not in db_case_numbers:
                session.add(
                    Cases(case_number=case_number, project_id=project_id)
                )
                logging.info(
                    f"Добавлено дело: {case_number} с project_id: {project_id}"
                )
                added += 1

        for case_number in db_case_numbers:
            if case_number not in active_case_numbers:
                obj = session.query(Cases).filter_by(
                    case_number=case_number
                ).first()
                if obj:
                    session.delete(obj)
                    logging.info(f"Удалено архивное дело: {case_number}")

        session.commit()
        logging.info(f"Итого добавлено: {added}")
    except Exception as e:
        logging.error(f"Ошибка синхронизации CRM: {e}")
        session.rollback()
    finally:
        session.close()

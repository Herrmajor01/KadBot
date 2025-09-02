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
    format="%(asctime)s - %(levelname)s - %(message)s",
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

        # Диагностика: проверяем дублирующиеся project_id в CRM
        project_id_counts = {}
        for proj in active_projects:
            project_id = proj.get("id")
            if project_id:
                if project_id not in project_id_counts:
                    project_id_counts[project_id] = []
                project_id_counts[project_id].append(proj.get("name", ""))

        duplicates = {
            pid: names for pid, names in project_id_counts.items()
            if len(names) > 1
        }
        if duplicates:
            logging.warning(
                f"Найдены дублирующиеся project_id в CRM: {duplicates}"
            )
            # Детальная диагностика для каждого дубликата
            for pid, names in duplicates.items():
                logging.warning(
                    f"Project_id {pid} используется в проектах: {names}"
                )

        # Дополнительная диагностика для проблемных project_id
        problematic_ids = [1275, 1337]  # Добавляем другие проблемные ID
        for pid in problematic_ids:
            if pid in project_id_counts:
                logging.info(
                    f"Project_id {pid} найден в CRM в проектах: "
                    f"{project_id_counts[pid]}"
                )

        # Получаем существующие записи из БД
        db_cases = {c.case_number: c for c in session.query(Cases).all()}
        db_project_ids = {c.project_id for c in db_cases.values()}
        active_case_numbers = set()
        added = 0
        updated = 0
        conflicts = 0

        for proj in active_projects:
            name = proj.get("name", "")
            case_number = extract_case_number(name)
            if not case_number:
                continue
            project_id = proj.get("id")
            active_case_numbers.add(case_number)

            # Проверяем, есть ли уже такое дело в БД
            if case_number in db_cases:
                existing_case = db_cases[case_number]
                # Если project_id изменился, обновляем
                if existing_case.project_id != project_id:
                    # Проверяем, не занят ли новый project_id другим делом
                    if project_id in db_project_ids:
                        logging.warning(
                            f"Конфликт: дело {case_number} пытается "
                            f"использовать project_id {project_id}, который "
                            f"уже занят другим делом"
                        )
                        conflicts += 1
                        continue
                    existing_case.project_id = project_id
                    updated += 1
                    logging.info(
                        f"Обновлен project_id для дела {case_number}: "
                        f"{existing_case.project_id} -> {project_id}"
                    )
            else:
                # Новое дело
                if project_id in db_project_ids:
                    logging.warning(
                        f"Конфликт: новое дело {case_number} пытается "
                        f"использовать project_id {project_id}, который "
                        f"уже занят"
                    )
                    conflicts += 1
                    continue

                session.add(
                    Cases(case_number=case_number, project_id=project_id)
                )
                db_project_ids.add(project_id)
                logging.info(
                    f"Добавлено дело: {case_number} с project_id: {project_id}"
                )
                added += 1

        # Удаляем архивные дела
        removed = 0
        for case_number in db_cases:
            if case_number not in active_case_numbers:
                obj = db_cases[case_number]
                session.delete(obj)
                logging.info(f"Удалено архивное дело: {case_number}")
                removed += 1

        session.commit()
        logging.info(
            f"Итого добавлено: {added}, обновлено: {updated}, "
            f"удалено: {removed}, конфликтов: {conflicts}"
        )
    except Exception as e:
        logging.error(f"Ошибка синхронизации CRM: {e}")
        session.rollback()
    finally:
        session.close()


if __name__ == "__main__":
    """
    Точка входа для выполнения синхронизации проектов из CRM.
    """
    sync_crm_projects_to_db()

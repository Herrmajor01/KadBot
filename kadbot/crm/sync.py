"""
Модуль для синхронизации проектов из Aspro CRM с базой данных.
Извлекает номера дел из названий проектов и обновляет базу данных.
Теперь использует централизованный конфиг и CRM‑клиент.
"""

import logging
import re
from typing import Any, Dict, List, Optional

from kadbot.config import get_config
from kadbot.crm.client import AsproClient
from kadbot.db.session import Session
from kadbot.db.models import Cases

logger = logging.getLogger(__name__)


def get_projects() -> List[Dict[str, Any]]:
    """
    Получает список всех проектов из Aspro CRM через API.

    Returns:
        List[Dict]: Список проектов с их данными
    """
    cfg = get_config()
    client = AsproClient(cfg.aspro_api_key, cfg.aspro_company)
    projects: List[Dict[str, Any]] = []
    page = 1
    while True:
        resp = client.get(f"/module/st/projects/list", params={"page": str(page)})
        if not resp.ok:
            logger.error("Ошибка получения списка проектов: %s - %s", resp.status_code, resp.text)
            break
        data = resp.json()
        items = data.get("response", {}).get("items", [])
        total = data.get("response", {}).get("total", 0)
        if not items:
            break
        projects.extend(items)
        if len(projects) >= total:
            break
        page += 1
    return projects


def _is_archived(value: Any) -> bool:
    """Нормализует признак архива в bool.

    Aspro может возвращать 0/1, True/False, "0"/"1", "true"/"false".
    """
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return int(value) != 0
    if isinstance(value, str):
        v = value.strip().lower()
        if v in {"1", "true", "yes", "y"}:
            return True
        if v in {"0", "false", "no", "n", ""}:
            return False
        # Непредвиденное значение считаем ложным
        return False
    return bool(value)


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
        active_projects = [p for p in all_projects if not _is_archived(p.get("is_archive", 0))]
        logger.info(f"Всего проектов в CRM: {len(all_projects)}")
        logger.info(f"Новых, неархивных проектов: {len(active_projects)}")

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
            logger.warning(
                f"Найдены дублирующиеся project_id в CRM: {duplicates}"
            )
            # Детальная диагностика для каждого дубликата
            for pid, names in duplicates.items():
                logger.warning(
                    f"Project_id {pid} используется в проектах: {names}"
                )

        # Дополнительная диагностика для проблемных project_id
        problematic_ids = [1275, 1337]  # Добавляем другие проблемные ID
        for pid in problematic_ids:
            if pid in project_id_counts:
                logger.info(
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
                        logger.warning(
                            f"Конфликт: дело {case_number} пытается "
                            f"использовать project_id {project_id}, который "
                            f"уже занят другим делом"
                        )
                        conflicts += 1
                        continue
                    existing_case.project_id = project_id
                    updated += 1
                    logger.info(
                        f"Обновлен project_id для дела {case_number}: "
                        f"{existing_case.project_id} -> {project_id}"
                    )
                # Помечаем как активный
                if getattr(existing_case, "is_active", True) is False:
                    existing_case.is_active = True
            else:
                # Новое дело
                if project_id in db_project_ids:
                    logger.warning(
                        f"Конфликт: новое дело {case_number} пытается "
                        f"использовать project_id {project_id}, который "
                        f"уже занят"
                    )
                    conflicts += 1
                    continue

                session.add(
                    Cases(case_number=case_number, project_id=project_id, is_active=True)
                )
                db_project_ids.add(project_id)
                logger.info(
                    f"Добавлено дело: {case_number} с project_id: {project_id}"
                )
                added += 1

        # Помечаем архивные дела как неактивные (soft delete)
        removed = 0
        for case_number in db_cases:
            if case_number not in active_case_numbers:
                obj = db_cases[case_number]
                if getattr(obj, "is_active", True):
                    obj.is_active = False
                    logger.info(f"Помечено архивное дело как неактивное: {case_number}")
                    removed += 1

        session.commit()
        logger.info(
            f"Итого добавлено: {added}, обновлено: {updated}, "
            f"удалено: {removed}, конфликтов: {conflicts}"
        )
    except Exception as e:
        logger.error(f"Ошибка синхронизации CRM: {e}")
        session.rollback()
    finally:
        session.close()


if __name__ == "__main__":
    """
    Точка входа для выполнения синхронизации проектов из CRM.
    """
    sync_crm_projects_to_db()

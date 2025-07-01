"""
Модуль для отправки уведомлений в Aspro CRM через API.
"""

import logging
import os
from typing import Optional

import requests  # type: ignore
from dotenv import load_dotenv  # type: ignore

logging.basicConfig(
    filename="kad_parser.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)

load_dotenv()
ASPRO_API_KEY = os.getenv("ASPRO_API_KEY")
COMPANY = os.getenv("ASPRO_COMPANY")
USERID = os.getenv("USERID")
USER_NAME = os.getenv("USER_NAME")
MODULE = "st"
ENTITY = "projects"


def send_case_update_comment(
    project_id: int,
    event_title: str,
    event_date: str,
    doc_link: Optional[str] = None,
) -> Optional[dict]:
    """
    Отправляет комментарий-уведомление об обновлении события по делу в проект
    Aspro CRM с упоминанием пользователя.

    Args:
        project_id: ID проекта в CRM
        event_title: Название события
        event_date: Дата события
        doc_link: Ссылка на документ (опционально)

    Returns:
        dict: Ответ API при успешной отправке, None при ошибке
    """
    if not project_id:
        logging.error("Не указан project_id!")
        return None

    if not ASPRO_API_KEY or not COMPANY:
        logging.error(
            "Переменные ASPRO_API_KEY или ASPRO_COMPANY не заданы в .env"
        )
        return None

    if not USERID:
        logging.error("Переменная USERID не задана в .env")
        return None

    if not USER_NAME:
        logging.error("Переменная USER_NAME не задана в .env")
        return None

    comment_text = (
        f"<p>Обновление по делу<br>"
        f'Уведомление для: <span class="js-item-mention '
        f'mentioning__user flw--comment-mention" '
        f'data-id="{USERID}" data-user-detail="" '
        f'data-user-id="{USERID}" '
        f'data-href="/_module/company/view/member/{USERID}" '
        f'data-toggle="sidepanel" '
        f'_target="blank" contenteditable="false">{USER_NAME}</span><br>'
        f"Событие: <b>{event_title}</b><br>"
        f"Дата: {event_date}<br>"
        f"<a href='{doc_link if doc_link else '#'}'>Документ</a></p>"
    )

    url = (
        f"https://{COMPANY}.aspro.cloud/api/v1/module/{MODULE}/"
        f"{ENTITY}/{project_id}/comments/create"
    )
    params = {"api_key": ASPRO_API_KEY}
    data = {"text": comment_text}
    headers = {"content-type": "application/x-www-form-urlencoded"}

    try:
        response = requests.post(
            url, params=params, data=data, headers=headers, timeout=10
        )
        if response.ok:
            logging.info("Комментарий успешно отправлен в CRM")
            return response.json()
        else:
            logging.error(
                f"Ошибка отправки комментария: {response.status_code} - "
                f"{response.text}"
            )
            return None
    except Exception as e:
        logging.error(f"Ошибка при попытке отправки комментария: {e}")
        return None

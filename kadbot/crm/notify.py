"""
Модуль для отправки уведомлений в Aspro CRM через API.
Теперь использует централизованный конфиг и CRM‑клиент с ретраями.
"""

import html
import logging
from typing import Optional

from kadbot.config import get_config
from kadbot.crm.client import AsproClient

logger = logging.getLogger(__name__)

MODULE = "st"
ENTITY = "projects"


def build_comment_text(event_title: str, event_date: str, doc_link: Optional[str]) -> str:
    """Строит HTML-текст комментария для CRM с безопасным экранированием.

    Возвращает готовую строку для Aspro CRM.
    """
    cfg = get_config()
    safe_title = html.escape(event_title or "")
    safe_date = html.escape(event_date or "")
    safe_user = html.escape(cfg.user_name)
    safe_link = html.escape(doc_link) if doc_link else "#"

    comment_text = (
        f"<p>Обновление по делу<br>"
        f'Уведомление для: <span class="js-item-mention '
        f'mentioning__user flw--comment-mention" '
        f'data-id="{cfg.user_id}" data-user-detail="" '
        f'data-user-id="{cfg.user_id}" '
        f'data-href="/_module/company/view/member/{cfg.user_id}" '
        f'data-toggle="sidepanel" '
        f'_target="blank" contenteditable="false">{safe_user}</span><br>'
        f"Событие: <b>{safe_title}</b><br>"
        f"Дата: {safe_date}<br>"
        f"<a href='{safe_link}'>Документ</a></p>"
    )
    return comment_text


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
        logger.error("Не указан project_id!")
        return None

    cfg = get_config()
    if not cfg.aspro_api_key or not cfg.aspro_company:
        logger.error("Переменные ASPRO_API_KEY или ASPRO_COMPANY не заданы в .env")
        return None

    if not cfg.user_id:
        logger.error("Переменная USERID не задана в .env")
        return None

    if not cfg.user_name:
        logger.error("Переменная USER_NAME не задана в .env")
        return None

    comment_text = build_comment_text(event_title, event_date, doc_link)

    try:
        client = AsproClient(cfg.aspro_api_key, cfg.aspro_company)
        result = client.create_comment(MODULE, ENTITY, project_id, comment_text)
        if result is not None:
            logger.info("Комментарий успешно отправлен в CRM")
            return result
        logger.error("Ошибка при отправке комментария в CRM")
        return None
    except Exception as e:
        logger.error(f"Ошибка при попытке отправки комментария: {e}")
        return None

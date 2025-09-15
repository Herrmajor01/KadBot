"""
Модуль для создания событий календаря в Aspro.Cloud
Теперь использует централизованный конфиг и CRM‑клиент.
"""

import logging
from datetime import datetime, timedelta
from typing import Optional

from kadbot.config import get_config
from kadbot.crm.client import AsproClient

logger = logging.getLogger(__name__)


def _format_dt(dt: datetime) -> str:
    # API ожидает формат YYYY-MM-DD hh:mm:ss
    return dt.strftime("%Y-%m-%d %H:%M:%S")


# Кеш для ID календаря "Судебные заседания"
hearings_cal_id_cache: Optional[int] = None


def _get_or_create_hearings_calendar() -> Optional[int]:
    """
    Возвращает ID календаря "Судебные заседания". Если календарь удалён,
    пытается найти его в списке, а при отсутствии — создаёт заново.

    Returns:
        int | None: ID календаря или None при ошибке
    """
    global hearings_cal_id_cache

    if hearings_cal_id_cache is not None:
        return hearings_cal_id_cache

    cfg = get_config()
    if not cfg.aspro_api_key or not cfg.aspro_company:
        logger.error("ASPRO_API_KEY/ASPRO_COMPANY не заданы. Не могу получить календарь.")
        return None

    # 1) Если указан ID через переменную окружения — используем его как приоритетный
    if cfg.aspro_event_calendar_id:
        hearings_cal_id_cache = cfg.aspro_event_calendar_id
        logger.info("Использую ID календаря из ASPRO_EVENT_CALENDAR_ID: %s", cfg.aspro_event_calendar_id)
        return hearings_cal_id_cache

    client = AsproClient(cfg.aspro_api_key, cfg.aspro_company)

    # 2) Пытаемся найти нужный календарь по имени через список
    try:
        data = client.list_calendars()
        if data:
            items = data.get("response", {}).get("items", [])
            target_names = {"Судебные заседания", "Зудебные заседания"}
            for item in items:
                name = str(item.get("name", "")).strip()
                if name in target_names:
                    hearings_cal_id_cache = int(item.get("id"))
                    logger.info("Найден календарь '%s' с ID %s", name, hearings_cal_id_cache)
                    return hearings_cal_id_cache
    except Exception as e:
        logger.error("Исключение при получении списка календарей: %s", str(e))

    # 3) Если не нашли — создаем заново с корректным именем
    try:
        created = client.create_calendar(
            name="Судебные заседания",
            description="Календарь для судебных заседаний (создан KadBot)",
            type_=20,
            color="#FF0000",
            timezone="Europe/Moscow",
        )
        if created:
            cal_id = int(created.get("response", {}).get("id"))
            hearings_cal_id_cache = cal_id
            logger.info("Создан календарь 'Судебные заседания' с ID %s", cal_id)
            return cal_id
        return None
    except Exception as e:
        logger.error("Исключение при создании календаря: %s", str(e))
        return None


def create_project_calendar_event(
    project_id: int,
    case_number: str,
    start_dt: datetime,
    duration_minutes: int = 60,
    room: Optional[str] = None,
    event_calendar_id: Optional[int] = None,
) -> Optional[dict[str, object]]:
    """
    Создаёт событие календаря, связанное с проектом.

    Args:
        project_id: ID проекта в CRM
        case_number: Номер дела
        start_dt: Дата и время начала заседания
        duration_minutes: Продолжительность в минутах (по умолчанию 60)
        room: Номер кабинета/зала (опционально)

    Returns:
        Ответ API или None при ошибке
    """
    cfg = get_config()
    if not cfg.aspro_api_key or not cfg.aspro_company:
        logger.error("ASPRO_API_KEY/ASPRO_COMPANY не заданы. Не могу создать событие.")
        return None

    logger.info(
        "Создаю событие календаря для дела %s (проект %d) на %s",
        case_number,
        project_id,
        start_dt.strftime("%d.%m.%Y %H:%M"),
    )

    try:
        # Вычисляем время окончания события
        end_dt = start_dt + timedelta(minutes=duration_minutes)

        # Получаем/создаём ID календаря для судебных заседаний,
        # если не передан явно
        calendar_id = (
            event_calendar_id
            if event_calendar_id is not None
            else _get_or_create_hearings_calendar()
        )
        if not calendar_id:
            logger.error("Не удалось получить ID календаря для события")
            return None

        client = AsproClient(cfg.aspro_api_key, cfg.aspro_company)

        # Данные для создания события в календаре
        description = (
            "Автоматически добавлено из KadBot\n" +
            f"Дело: {case_number}"
        )
        if room:
            description = description + f"\nКабинет: {room}"

        data = {
            "name": f"Судебное заседание по делу {case_number}",
            "description": description,
            "type": 20,  # Событие (не задача)
            "event_calendar_id": calendar_id,
            "plan_start_date": start_dt.strftime("%Y-%m-%d %H:%M:%S"),
            "plan_end_date": end_dt.strftime("%Y-%m-%d %H:%M:%S"),
            "event_color": "#FF0000",  # Красный цвет для судебных заседаний
            "event_busy_status": 20,  # Занят
            "event_access_type": 30,  # Публичное событие
            "all_day": 0,  # Не на весь день
            "module": "st",  # Модуль "Проекты"
            "model": "project",  # Модель "Проект"
            "model_id": project_id,  # ID проекта для привязки
        }

        # Отдельно логируем дату и время, отправляемые в календарь CRM
        logger.info(
            "Отправляю в календарь ЦРМ дату/время заседания: %s — %s (дело %s, проект %d, календарь %s)",
            data["plan_start_date"],
            data["plan_end_date"],
            case_number,
            project_id,
            str(calendar_id),
        )

        logger.info("Отправляю запрос на создание события в CRM")
        logger.debug("Данные события: %s", data)

        result = client.create_task_event(data)
        if result:
            logger.info(
                "Событие календаря успешно создано в CRM для дела %s (ID: %s). Дата/время: %s — %s",
                case_number,
                result.get("response", {}).get("id", "неизвестно"),
                data["plan_start_date"],
                data["plan_end_date"],
            )
            return result
        logger.error("Ошибка создания события календаря для дела %s", case_number)
        return None

    except Exception as e:
        logger.error(
            "Исключение при создании события календаря для дела %s: %s",
            case_number,
            str(e),
            exc_info=True,
        )
        return None


def test_calendar_api() -> None:
    """
    Тестовая функция для проверки API календаря.
    """
    logger.info("Запуск теста API календаря")

    cfg = get_config()
    if not cfg.aspro_api_key or not cfg.aspro_company:
        logger.error("Тест пропущен: не заданы ASPRO_API_KEY/ASPRO_COMPANY")
        return

    try:
        # Тестируем создание события
        test_dt = datetime.now() + timedelta(days=1)
        result = create_project_calendar_event(
            project_id=999,  # Тестовый ID
            case_number="TEST-001",
            start_dt=test_dt,
            duration_minutes=90,
            room="к.316",
        )

        if result:
            logger.info("Тест API календаря пройден успешно")
        else:
            logger.error("Тест API календаря не пройден")

    except Exception as e:
        logger.error("Ошибка в тесте API календаря: %s", str(e), exc_info=True)


if __name__ == "__main__":
    # Запуск теста при прямом вызове модуля
    test_calendar_api()

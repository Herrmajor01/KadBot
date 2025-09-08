"""
Модуль для создания событий календаря в Aspro.Cloud
"""

import logging
import os
from datetime import datetime, timedelta
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

# ID календаря, куда создаём событие (получить в CRM). Опционально
ASPRO_EVENT_CALENDAR_ID = os.getenv("ASPRO_EVENT_CALENDAR_ID")


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

    if not ASPRO_API_KEY or not COMPANY:
        logging.error(
            "ASPRO_API_KEY/ASPRO_COMPANY не заданы. Не могу получить "
            "календарь."
        )
        return None

    # 1) Если указан ID через переменную окружения — используем его как приоритетный
    if ASPRO_EVENT_CALENDAR_ID:
        try:
            cal_id = int(ASPRO_EVENT_CALENDAR_ID)
            hearings_cal_id_cache = cal_id
            logging.info(
                "Использую ID календаря из переменной "
                "ASPRO_EVENT_CALENDAR_ID: %s",
                cal_id,
            )
            return cal_id
        except ValueError:
            logging.warning(
                "ASPRO_EVENT_CALENDAR_ID имеет неверный формат: %s",
                ASPRO_EVENT_CALENDAR_ID,
            )

    # 2) Пытаемся найти нужный календарь по имени через список
    try:
        list_url = (
            "https://" + COMPANY + ".aspro.cloud/api/v1/module/calendar/" +
            "calendar/list"
        )
        params = {"api_key": ASPRO_API_KEY}
        resp = requests.get(list_url, params=params, timeout=15)
        if resp.ok:
            items = resp.json().get("response", {}).get("items", [])
            target_names = {"Судебные заседания", "Зудебные заседания"}
            for item in items:
                name = str(item.get("name", "")).strip()
                if name in target_names:
                    hearings_cal_id_cache = int(item.get("id"))
                    logging.info(
                        "Найден календарь '%s' с ID %s",
                        name,
                        hearings_cal_id_cache,
                    )
                    return hearings_cal_id_cache
        else:
            logging.error(
                "Ошибка запроса списка календарей: HTTP %d - %s",
                resp.status_code,
                resp.text,
            )
    except Exception as e:
        logging.error("Исключение при получении списка календарей: %s", str(e))

    # 3) Если не нашли — создаем заново с корректным именем
    try:
        create_url = (
            "https://" + COMPANY + ".aspro.cloud/api/v1/module/calendar/" +
            "calendar/create"
        )
        params = {"api_key": ASPRO_API_KEY}
        data = {
            "name": "Судебные заседания",
            "description": "Календарь для судебных заседаний (создан KadBot)",
            "type": 20,  # Публичный
            "color": "#FF0000",
            "timezone": "Europe/Moscow",
        }
        resp = requests.post(create_url, params=params, data=data, timeout=15)
        if resp.ok:
            cal_id = int(resp.json().get("response", {}).get("id"))
            hearings_cal_id_cache = cal_id
            logging.info(
                "Создан календарь 'Судебные заседания' с ID %s",
                cal_id,
            )
            return cal_id
        else:
            logging.error(
                "Ошибка создания календаря: HTTP %d - %s",
                resp.status_code,
                resp.text,
            )
            return None
    except Exception as e:
        logging.error("Исключение при создании календаря: %s", str(e))
        return None


def create_project_calendar_event(
    project_id: int,
    case_number: str,
    start_dt: datetime,
    duration_minutes: int = 60,
    room: Optional[str] = None,
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
    if not ASPRO_API_KEY or not COMPANY:
        logging.error(
            "ASPRO_API_KEY/ASPRO_COMPANY не заданы. Не могу создать событие."
        )
        return None

    logging.info(
        "Создаю событие календаря для дела %s (проект %d) на %s",
        case_number,
        project_id,
        start_dt.strftime("%d.%m.%Y %H:%M"),
    )

    try:
        # Вычисляем время окончания (пока не используется,
        # но может понадобиться)
        # end_dt = start_dt + timedelta(minutes=duration_minutes)

        # Получаем/создаём ID календаря для судебных заседаний
        calendar_id = _get_or_create_hearings_calendar()
        if not calendar_id:
            logging.error("Не удалось получить ID календаря для события")
            return None

        # Создаем событие в календаре через модуль "Задачи"
        url = (
            "https://" + COMPANY + ".aspro.cloud/api/v1/module/task/task/create"
        )

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
            "plan_end_date": start_dt.strftime("%Y-%m-%d %H:%M:%S"),
            "event_color": "#FF0000",  # Красный цвет для судебных заседаний
            "event_busy_status": 20,  # Занят
            "event_access_type": 30,  # Публичное событие
            "all_day": 0,  # Не на весь день
            "module": "st",  # Модуль "Проекты"
            "model": "project",  # Модель "Проект"
            "model_id": project_id,  # ID проекта для привязки
        }

        params = {"api_key": ASPRO_API_KEY}
        headers = {"Content-Type": "application/x-www-form-urlencoded"}

        logging.info(
            "Отправляю запрос на создание события: %s", url
        )
        logging.debug("Данные события: %s", data)

        resp = requests.post(
            url, params=params, data=data, headers=headers, timeout=15
        )

        if resp.ok:
            result = resp.json()
            logging.info(
                "Событие календаря успешно создано в CRM для дела %s. "
                "ID события: %s",
                case_number,
                result.get("response", {}).get("id", "неизвестно"),
            )
            return result
        else:
            logging.error(
                "Ошибка создания события календаря для дела %s: "
                "HTTP %d - %s",
                case_number,
                resp.status_code,
                resp.text,
            )
            return None

    except Exception as e:
        logging.error(
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
    logging.info("Запуск теста API календаря")

    if not ASPRO_API_KEY or not COMPANY:
        logging.error("Тест пропущен: не заданы ASPRO_API_KEY/ASPRO_COMPANY")
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
            logging.info("Тест API календаря пройден успешно")
        else:
            logging.error("Тест API календаря не пройден")

    except Exception as e:
        logging.error("Ошибка в тесте API календаря: %s",
                      str(e), exc_info=True)


if __name__ == "__main__":
    # Запуск теста при прямом вызове модуля
    test_calendar_api()

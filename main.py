"""
Главный модуль приложения для парсинга дел.
Предоставляет интерфейс для выбора действий: синхронизация CRM или парсинг.
"""
from parser import sync_chronology  # type: ignore

from crm_sync import sync_crm_projects_to_db


def main() -> None:
    """
    Главная функция приложения.

    Предоставляет пользователю выбор между синхронизацией проектов из CRM
    и парсингом событий по делам.
    """
    print("1. Синхронизировать CRM проекты")
    print("2. Парсить события по делам")
    action = input("Выбери действие (1 или 2): ").strip()

    if action == "1":
        sync_crm_projects_to_db()
    elif action == "2":
        sync_chronology()
    else:
        print("Неверный выбор!")


if __name__ == "__main__":
    """
    Точка входа в приложение.
    """
    main()

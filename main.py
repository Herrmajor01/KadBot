"""
Главный модуль приложения для парсинга дел и скачивания документов.
Предоставляет интерфейс для выбора действий: синхронизация CRM, парсинг или
скачивание документов.
"""
import json
import os
from parser import sync_chronology  # type: ignore

from crm_sync import sync_crm_projects_to_db
from download_documents import download_documents


def check_resume_option(filename: str) -> bool:
    """
    Проверяет, был ли предыдущий запуск процесса прерван, и предлагает
    пользователю выбор.

    Args:
        filename: Имя файла прогресса ('parser_progress.json' или
        'download_progress.json')

    Returns:
        bool: True, если пользователь выбрал продолжить, False, если начать
        заново
    """
    if os.path.exists(filename):
        with open(filename, "r", encoding="utf-8") as f:
            progress = json.load(f)
        last_case_number = progress.get("last_case_number", "неизвестно")
        process_name = (
            "парсинга" if filename == "parser_progress.json"
            else "скачивания документов"
        )
        print(
            f"\nОбнаружен прерванный процесс {process_name}. "
            f"Последнее обработанное дело: {last_case_number}"
        )
        print("1. Продолжить с последнего обработанного дела")
        print("2. Начать заново")
        choice = input("Выберите действие (1 или 2): ").strip()
        return choice == "1"
    return False


def main() -> None:
    """
    Главная функция приложения.

    Предоставляет пользователю выбор между синхронизацией проектов из CRM,
    парсингом событий по делам или скачиванием документов. Поддерживает
    возобновление.
    """
    print("1. Синхронизировать CRM проекты")
    print("2. Парсить события по делам")
    print("3. Скачать документы по ссылкам из базы данных")
    action = input(
        "Выбери действие (1, 2 или 3): "
    ).strip()

    if action == "1":
        sync_crm_projects_to_db()
    elif action == "2":
        resume = check_resume_option("parser_progress.json")
        sync_chronology(resume=resume)
    elif action == "3":
        resume = check_resume_option("download_progress.json")
        download_documents(resume=resume)
    else:
        print("Неверный выбор!")


if __name__ == "__main__":
    """
    Точка входа в приложение.
    """
    main()

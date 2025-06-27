from logic import main_process_cases
from crm_sync import sync_crm_projects_to_db  # type: ignore


def main():
    print("1. Синхронизировать CRM проекты")
    print("2. Парсить хронологии дел")
    choice = input("Выбери действие (1 или 2): ")

    if choice == "1":
        sync_crm_projects_to_db()
    elif choice == "2":
        main_process_cases()
    else:
        print("Неизвестный выбор!")


if __name__ == "__main__":
    main()

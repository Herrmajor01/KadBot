"""
Модуль для инициализации базы данных.
Создает все таблицы на основе моделей SQLAlchemy.
"""
from db import engine
from models import Base


def init_db() -> None:
    """
    Создает все таблицы в базе данных на основе метаданных моделей.

    Использует engine из модуля db и Base из модуля models для создания
    всех таблиц, определенных в моделях SQLAlchemy.
    """
    Base.metadata.create_all(engine)


if __name__ == "__main__":
    """
    Точка входа для инициализации базы данных.
    """
    init_db()
    print("База данных и таблицы созданы.")

"""
Модуль для миграции базы данных.
Добавляет новые столбцы в существующие таблицы при необходимости.
"""

import logging
import os

from dotenv import load_dotenv  # type: ignore
from sqlalchemy import MetaData, Table, create_engine  # type: ignore
from sqlalchemy.sql import text  # type: ignore

logging.basicConfig(
    filename="kad_parser.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///kad_cases.db")


def migrate_db() -> None:
    """
    Выполняет миграцию базы данных.

    Добавляет столбец project_id в таблицу cases, если он отсутствует.
    """
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {},
    )
    metadata = MetaData()
    metadata.reflect(bind=engine)

    cases_table = Table("cases", metadata, autoload_with=engine)

    if "project_id" not in cases_table.c:
        logging.info("Добавление столбца project_id в таблицу cases")
        with engine.connect() as conn:
            conn.execute(
                text("ALTER TABLE cases ADD COLUMN project_id INTEGER")
            )
            conn.commit()
        logging.info("Столбец project_id успешно добавлен")
    else:
        logging.info("Столбец project_id уже существует")

    # Добавить флаг is_active, если отсутствует
    if "is_active" not in cases_table.c:
        logging.info("Добавление столбца is_active в таблицу cases")
        with engine.connect() as conn:
            conn.execute(text("ALTER TABLE cases ADD COLUMN is_active INTEGER DEFAULT 1"))
            # Установим 1 (True) для всех текущих записей
            conn.execute(text("UPDATE cases SET is_active = 1 WHERE is_active IS NULL"))
            conn.commit()
        logging.info("Столбец is_active успешно добавлен и инициализирован")
    else:
        logging.info("Столбец is_active уже существует")

    # Миграция таблицы chronology: добавить hearing_event_id (TEXT)
    chronology_table = Table("chronology", metadata, autoload_with=engine)
    if "hearing_event_id" not in chronology_table.c:
        logging.info("Добавление столбца hearing_event_id в таблицу chronology")
        with engine.connect() as conn:
            conn.execute(
                text("ALTER TABLE chronology ADD COLUMN hearing_event_id TEXT")
            )
            conn.commit()
        logging.info("Столбец hearing_event_id успешно добавлен")
    else:
        logging.info("Столбец hearing_event_id уже существует")


if __name__ == "__main__":
    """
    Точка входа для выполнения миграции базы данных.
    """
    migrate_db()

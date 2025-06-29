"""
Модуль для миграции базы данных.
Добавляет новые столбцы в существующие таблицы при необходимости.
"""
import logging

from sqlalchemy import MetaData, Table, create_engine  # type: ignore
from sqlalchemy.sql import text  # type: ignore

logging.basicConfig(
    filename="kad_parser.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

DB_PATH = "sqlite:///kad_cases.db"


def migrate_db() -> None:
    """
    Выполняет миграцию базы данных.

    Добавляет столбец project_id в таблицу cases, если он отсутствует.
    """
    engine = create_engine(
        DB_PATH,
        connect_args={'check_same_thread': False}
    )
    metadata = MetaData()
    metadata.reflect(bind=engine)

    cases_table = Table('cases', metadata, autoload_with=engine)

    if 'project_id' not in cases_table.c:
        logging.info("Добавление столбца project_id в таблицу cases")
        with engine.connect() as conn:
            conn.execute(
                text('ALTER TABLE cases ADD COLUMN project_id INTEGER')
            )
            conn.commit()
        logging.info("Столбец project_id успешно добавлен")
    else:
        logging.info("Столбец project_id уже существует")


if __name__ == "__main__":
    """
    Точка входа для выполнения миграции базы данных.
    """
    migrate_db()

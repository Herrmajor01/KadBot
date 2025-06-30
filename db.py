"""
Модуль для работы с базой данных SQLAlchemy.
Содержит настройки подключения и функции для работы с данными.
"""
from typing import Optional

from sqlalchemy import create_engine  # type: ignore
from sqlalchemy.orm import sessionmaker  # type: ignore

from models import Cases

DB_PATH = "sqlite:///kad_cases.db"

engine = create_engine(DB_PATH, connect_args={'check_same_thread': False})
Session = sessionmaker(bind=engine)


def get_project_id_for_case(case_number: str) -> Optional[int]:
    """
    Получает project_id для указанного номера дела из базы данных.

    Args:
        case_number: Номер дела

    Returns:
        int: ID проекта в CRM или None, если дело не найдено
    """
    session = Session()
    try:
        case = session.query(Cases).filter_by(case_number=case_number).first()
        return case.project_id if case else None
    finally:
        session.close()

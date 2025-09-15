"""
Модуль для работы с базой данных SQLAlchemy.
Содержит настройки подключения и функции для работы с данными.
"""

import os
from typing import Optional

from dotenv import load_dotenv  # type: ignore
from sqlalchemy import create_engine  # type: ignore
from sqlalchemy.orm import sessionmaker  # type: ignore

from kadbot.db.models import Cases

# Загружаем переменные окружения и определяем URL базы данных
load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///kad_cases.db")

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {})
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
        q = session.query(Cases).filter_by(case_number=case_number)
        try:
            # Если колонка is_active присутствует — фильтруем по активным
            q = q.filter(Cases.is_active == True)  # type: ignore[attr-defined]  # noqa: E712
        except Exception:
            pass
        case = q.first()
        return case.project_id if case else None
    finally:
        session.close()

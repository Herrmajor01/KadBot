"""
Модели SQLAlchemy для работы с базой данных.
Определяет структуру таблиц для дел и хронологии событий.
"""

from sqlalchemy import Column, Integer, String, Boolean  # type: ignore
from sqlalchemy.ext.declarative import declarative_base  # type: ignore

Base = declarative_base()


class Cases(Base):
    """
    Модель для хранения информации о делах.

    Связывает номера дел с ID проектов в CRM системе.
    """

    __tablename__ = "cases"
    id = Column(Integer, primary_key=True)
    case_number = Column(String, unique=True, nullable=False)
    project_id = Column(Integer, unique=True, index=True)
    # Флаг активности проекта в CRM (soft delete)
    is_active = Column(Boolean, default=True, index=True)


class Chronology(Base):
    """
    Модель для хранения хронологии событий по делам.

    Содержит информацию о событиях, датах, авторах и ссылках на документы.
    """

    __tablename__ = "chronology"
    id = Column(Integer, primary_key=True)
    case_number = Column(String, nullable=False)
    event_date = Column(String)
    event_title = Column(String)
    event_author = Column(String)
    event_publish = Column(String)
    events_count = Column(Integer)
    doc_link = Column(String)
    # Новые поля для информации о заседании
    hearing_date = Column(String)  # Дата заседания в формате DD.MM.YYYY
    hearing_time = Column(String)  # Время заседания в формате HH:MM
    hearing_room = Column(String)  # Номер кабинета/зала
    # Когда было создано событие в календаре
    hearing_created_at = Column(String)
    # ID события календаря в CRM (для идемпотентности/обновлений)
    hearing_event_id = Column(String)

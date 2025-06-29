"""
Модели SQLAlchemy для работы с базой данных.
Определяет структуру таблиц для дел и хронологии событий.
"""
from sqlalchemy import Column, Integer, String  # type: ignore
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

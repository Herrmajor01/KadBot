from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String

Base = declarative_base()


class Cases(Base):
    __tablename__ = "cases"
    id = Column(Integer, primary_key=True)
    case_number = Column(String, unique=True, nullable=False)


class Chronology(Base):
    __tablename__ = "chronology"
    id = Column(Integer, primary_key=True)
    case_number = Column(String, nullable=False)
    event_date = Column(String)
    event_title = Column(String)
    event_author = Column(String)
    event_publish = Column(String)
    events_count = Column(Integer)
    doc_link = Column(String)

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base

DB_PATH = "sqlite:///kad_cases.db"

engine = create_engine(DB_PATH, connect_args={'check_same_thread': False})
Session = sessionmaker(bind=engine)

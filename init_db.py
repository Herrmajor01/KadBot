from db import engine
from models import Base


def init_db():
    Base.metadata.create_all(engine)


if __name__ == "__main__":
    init_db()
    print("База данных и таблицы созданы.")

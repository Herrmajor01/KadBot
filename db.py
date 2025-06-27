"""
Операции с базой данных для KadBot: обработка дел и событий хронологии.
"""

import sqlite3

DB_PATH = "kad_cases.db"


def get_case_numbers():
    """
    Получить список номеров дел из таблицы cases.
    """
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT case_number FROM cases")
    res = [row[0] for row in c.fetchall()]
    conn.close()
    return res


def get_last_event(case_number):
    """
    Возвращает последнее событие по делу как словарь
    или None, если нет события.
    """
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(
        "SELECT event_date, event_title, event_author, event_publish, "
        "events_count, doc_link "
        "FROM chronology WHERE case_number = ? "
        "ORDER BY event_date DESC LIMIT 1",
        (case_number,)
    )
    row = c.fetchone()
    conn.close()
    if row:
        return {
            "event_date": row[0],
            "event_title": row[1],
            "event_author": row[2],
            "event_publish": row[3],
            "events_count": row[4],
            "doc_link": row[5]
        }
    else:
        return None


def save_event(
    case_number,
    event_date,
    event_title,
    event_author,
    event_publish,
    doc_link,
    events_count
):
    """
    Сохранить событие по делу. Если уже есть — перезаписать.
    """
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(
        "DELETE FROM chronology WHERE case_number=?",
        (case_number,)
    )
    c.execute(
        (
            "INSERT INTO chronology (case_number, event_date, event_title, "
            "event_author, event_publish, doc_link, events_count) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)"
        ),
        (case_number, event_date, event_title, event_author,
         event_publish, doc_link, events_count)
    )
    conn.commit()
    conn.close()

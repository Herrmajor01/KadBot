import sqlite3

DB_PATH = "kad_cases.db"


def get_case_numbers():
    """
    Получить список номеров дел из таблицы cases.
    """
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT case_number FROM cases")
    rows = c.fetchall()
    conn.close()
    return [row[0] for row in rows]


def get_last_event(case_number):
    """
    Получить последнее сохранённое событие по номеру дела.
    """
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(
        "SELECT event_date, event_title, event_author, "
        "event_publish, events_count FROM chronology "
        "WHERE case_number = ? ORDER BY event_date DESC LIMIT 1",
        (case_number,)
    )
    row = c.fetchone()
    conn.close()
    return row


def save_event(case_number, event_date, event_title,
               event_author, event_publish, events_count):
    """
    Сохранить событие по делу (заменить, если уже есть).
    """
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    # Удалить старое событие, если оно было
    c.execute(
        "DELETE FROM chronology WHERE case_number = ?",
        (case_number,)
    )
    c.execute(
        "INSERT INTO chronology (case_number, event_date, event_title, "
        "event_author, event_publish, events_count) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        (case_number, event_date, event_title,
         event_author, event_publish, events_count)
    )
    conn.commit()
    conn.close()

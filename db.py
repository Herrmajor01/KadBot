import sqlite3

DB_PATH = "kad_cases.db"


def get_case_numbers():
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        c.execute("SELECT case_number FROM cases")
        return [row[0] for row in c.fetchall()]


def get_last_event_for_case(case_number):
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        c.execute(
            "SELECT event_date, event_title FROM chronology WHERE case_number=?",
            (case_number,)
        )
        return c.fetchone()


def upsert_chronology(case_number, event_date, event_title, event_author, event_publish, events_count):
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        # Проверяем, есть ли уже запись
        c.execute(
            "SELECT id, event_date FROM chronology WHERE case_number=?", (case_number,))
        row = c.fetchone()
        if row is None:
            # Вставляем новую запись
            c.execute(
                "INSERT INTO chronology (case_number, event_date, event_title, event_author, event_publish, events_count) VALUES (?, ?, ?, ?, ?, ?)",
                (case_number, event_date, event_title,
                 event_author, event_publish, events_count)
            )
        else:
            # Проверяем, не свежее ли новое событие
            old_event_date = row[1]
            if event_date > (old_event_date or ""):
                c.execute(
                    "UPDATE chronology SET event_date=?, event_title=?, event_author=?, event_publish=?, events_count=? WHERE case_number=?",
                    (event_date, event_title, event_author,
                     event_publish, events_count, case_number)
                )

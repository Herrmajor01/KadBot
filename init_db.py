"""Этот модуль инициализирует базу данных SQLite и создает необходимые таблицы для KadBot."""

import sqlite3

conn = sqlite3.connect("kad_cases.db")
c = conn.cursor()
c.execute(
    "CREATE TABLE IF NOT EXISTS cases ("
    "id INTEGER PRIMARY KEY AUTOINCREMENT,"
    "case_number TEXT UNIQUE)"
)
c.execute(
    "CREATE TABLE IF NOT EXISTS chronology ("
    "id INTEGER PRIMARY KEY AUTOINCREMENT,"
    "case_number TEXT,"
    "event_date TEXT,"
    "event_title TEXT,"
    "event_author TEXT,"
    "event_publish TEXT,"
    "events_count INTEGER)"
)
conn.commit()
conn.close()

# KadBot 🤖

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

KadBot — сервис на Python для синхронизации проектов из Aspro.Cloud, парсинга событий по арбитражным делам с kad.arbitr.ru и скачивания документов с OCR. Текущая версия использует пакетную структуру `kadbot` и предоставляет CLI без интерактива.

## Возможности

- Синхронизация CRM: загрузка неархивных проектов Aspro.Cloud и обновление БД
- Парсинг дел: извлечение событий, «Следующее заседание» (дата/время/зал)
- Документы: скачивание PDF по ссылкам из БД, OCR в текст
- Уведомления: комментарии с упоминанием в проект Aspro.Cloud
- Календарь: создание событий заседаний в календаре CRM
- Надежность: возобновление прогресса, ретраи HTTP, пошаговые логи

## Требования

- Python 3.8+
- Google Chrome
- Tesseract OCR и poppler-utils (pdf2image)
- Доступ к API Aspro.Cloud

## Установка

1) Клонирование и окружение
```bash
git clone <repository-url>
cd KadBot
python3 -m venv venv
source venv/bin/activate  # Linux/macOS
# или
venv\Scripts\activate     # Windows
```

2) Зависимости
```bash
pip install -r requirements.txt
# Для разработки (опционально)
pip install -r requirements-dev.txt
pre-commit install
```

3) OCR и инструменты
```bash
# Ubuntu/Debian
sudo apt-get install -y tesseract-ocr tesseract-ocr-rus poppler-utils

# macOS (brew)
brew install tesseract tesseract-lang poppler
```

4) Конфигурация (.env)
Создайте файл `.env` в корне:
```env
ASPRO_API_KEY=ваш_api_ключ
ASPRO_COMPANY=идентификатор_компании
USERID=ид_пользователя_в_crm
USER_NAME=Имя_Пользователя

# Опционально
ASPRO_EVENT_CALENDAR_ID=49
DATABASE_URL=sqlite:///kad_cases.db
DOCUMENTS_DIR=/abs/path/to/documents
LOG_LEVEL=INFO
BROWSER_TIMEOUT=30
BROWSER_RETRIES=3
```

5) Инициализация/миграция БД
```bash
python -m kadbot.db.init_db
# при обновлении схемы
python -m kadbot.db.migrate
```

## Использование

### CLI без интерактива (рекомендуется)
```bash
# Синхронизация проектов из CRM
python -m kadbot.cli sync

# Парсинг хронологии (по умолчанию: batch_size=10, pause=5 сек)
python -m kadbot.cli parse --start-index 0 --batch-size 10 --pause-between-batches 5

# Скачивание документов (с OCR)
python -m kadbot.cli download --batch-size 10 --pause-between-batches 30 --resume

# Health‑check окружения/БД/CRM
python -m kadbot.cli health
python -m kadbot.cli health --skip-crm
```

Параметры по умолчанию соответствуют текущей реализации: `batch_size=10`, `pause_between_batches=5` для парсинга и `batch_size=10`, `pause_between_batches=30` для скачивания.

### Интерактивное меню
```bash
python main.py
```
Доступные действия: синхронизация CRM, парсинг дел, скачивание документов. Поддерживается восстановление прогресса.

## Архитектура

Структура ключевых модулей:
```
kadbot/
├── cli.py                 # CLI-команды: sync/parse/download/health
├── config.py              # Единый конфиг из .env
├── utils.py               # Драйвер Chrome, прогресс и утилиты
├── kad/
│   └── parser.py          # Парсер kad.arbitr.ru, sync_chronology()
├── services/
│   └── documents.py       # Скачать документы, OCR
├── crm/
│   ├── client.py          # HTTP‑клиент Aspro + ретраи
│   ├── sync.py            # Синхронизация проектов в БД
│   ├── notify.py          # Комментарии‑уведомления в проекты
│   └── calendar.py        # Создание событий календаря (заседания)
└── db/
    ├── models.py          # SQLAlchemy модели (Cases, Chronology)
    ├── session.py         # Подключение к БД, Session
    ├── init_db.py         # Создание таблиц
    └── migrate.py         # Миграции (project_id/is_active/hearing_event_id)

main.py                    # Интерактивное меню
```

### Модели данных (актуально)
```python
class Cases(Base):
    __tablename__ = "cases"
    id = Column(Integer, primary_key=True)
    case_number = Column(String, unique=True, nullable=False)
    project_id = Column(Integer, unique=True, index=True)
    is_active = Column(Boolean, default=True, index=True)

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
    hearing_date = Column(String)
    hearing_time = Column(String)
    hearing_room = Column(String)
    hearing_created_at = Column(String)
    hearing_event_id = Column(String)
```

## Мониторинг и диагностика

- Логи: `kad_parser.log` (tail -f, поиск ERROR/WARNING)
- База SQLite: `sqlite3 kad_cases.db ".schema"`
- Последние события: `sqlite3 kad_cases.db "SELECT * FROM chronology ORDER BY id DESC LIMIT 10;"`
- Документы: сохраняются в `DOCUMENTS_DIR` (по умолчанию `./documents`)

## Устранение неполадок

- Chrome: установите браузер и проверьте запуск `python -m kadbot.cli health`
- Tesseract: проверьте `tesseract --version` и наличие `tesseract-ocr-rus`
- API Aspro: проверьте переменные `ASPRO_API_KEY`, `ASPRO_COMPANY`
- Блокировки kad.arbitr.ru: увеличьте паузы, используйте разные User‑Agent

## Разработка

- Тесты: `pytest -q` (папка `tests/`)
- Форматирование/линтинг: black/isort/flake8 (см. `requirements-dev.txt`)
- Pre-commit: `pre-commit install`

## Лицензия

MIT. См. `LICENSE`.

— KadBot: автоматизация мониторинга арбитражных дел 🏛️

# KadBot API

## Обзор

KadBot предоставляет пакет `kadbot` с модулями для синхронизации проектов из Aspro.Cloud, парсинга событий дел с kad.arbitr.ru и скачивания документов. Ниже описаны публичные функции и точки входа.

## Быстрый старт (CLI)

```bash
python -m kadbot.cli sync                      # синхронизировать проекты из CRM
python -m kadbot.cli parse --batch-size 10     # спарсить хронологию
python -m kadbot.cli download --resume         # скачать документы + OCR
python -m kadbot.cli health [--skip-crm]       # проверить окружение
```

## Модули

### kadbot.kad.parser — парсер kad.arbitr.ru

- `parse_date(date_str: str) -> Optional[datetime]`
- `get_case_events(driver: uc.Chrome, case_number: str) -> Tuple[Optional[Dict[str, Any]], int]`
- `sync_chronology(start_index: int = 0, batch_size: int = 10, pause_between_batches: int = 5) -> None`

Пример:
```python
from kadbot.utils import get_driver
from kadbot.kad.parser import get_case_events, sync_chronology

driver = get_driver()
event, count = get_case_events(driver, "А32-29491/2023")
sync_chronology(batch_size=10, pause_between_batches=5)
```

### kadbot.services.documents — скачивание и OCR

- `download_document(driver, url: str, case_number: str, event_title: str, event_date: str, case_participants=None, output_dir: str = DEFAULT_DOCUMENTS_DIR) -> Optional[str]`
- `download_documents(batch_size: int = 10, pause_between_batches: int = 30, resume: bool = False) -> None`

Пример:
```python
from kadbot.services.documents import download_documents
download_documents(resume=True)
```

### kadbot.crm.sync — синхронизация CRM → БД

- `get_projects() -> list[dict]`
- `extract_case_number(name: str) -> Optional[str]`
- `sync_crm_projects_to_db() -> None`

Пример:
```python
from kadbot.crm.sync import sync_crm_projects_to_db
sync_crm_projects_to_db()
```

### kadbot.crm.notify — уведомления в Aspro

- `build_comment_text(event_title: str, event_date: str, doc_link: Optional[str]) -> str`
- `send_case_update_comment(project_id: int, event_title: str, event_date: str, doc_link: Optional[str] = None) -> Optional[dict]`

### kadbot.crm.calendar — события календаря Aspro

- `create_project_calendar_event(project_id: int, case_number: str, start_dt: datetime, duration_minutes: int = 60, room: Optional[str] = None, event_calendar_id: Optional[int] = None) -> Optional[dict]`

### kadbot.db.session — соединение с БД

- `Session` — сессия SQLAlchemy
- `engine` — подключение
- `get_project_id_for_case(case_number: str) -> Optional[int]`

### kadbot.db.models — модели SQLAlchemy

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

### kadbot.cli — точка входа CLI

- `main(argv: Optional[list[str]] = None) -> int` — команды: `sync`, `parse`, `download`, `health`

### kadbot.config — конфигурация

- `get_config() -> Config` — читает `.env`, кэширует

### kadbot.utils — утилиты

- `get_driver(retries: Optional[int] = None, timeout: Optional[int] = None) -> Optional[uc.Chrome]`
- `save_progress`, `load_progress`, `clear_progress`, `simulate_mouse_movement`

## Переменные окружения

`.env` (минимум):
```env
ASPRO_API_KEY=...
ASPRO_COMPANY=...
USERID=...
USER_NAME=...
```
Опционально: `ASPRO_EVENT_CALENDAR_ID`, `DATABASE_URL`, `DOCUMENTS_DIR`, `LOG_LEVEL`, `BROWSER_TIMEOUT`, `BROWSER_RETRIES`.

## Логи и ошибки

Лог-файл: `kad_parser.log`. При ошибках:
- проверяйте лог
- валидируйте `.env`
- проверяйте доступность kad.arbitr.ru и Aspro.Cloud

## Возобновление процессов

Поддерживается сохранение прогресса:
- `parser_progress.json` — парсинг
- `download_progress.json` — скачивание документов

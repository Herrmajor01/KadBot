# KadBot API Documentation

## Обзор

KadBot предоставляет набор модулей для автоматизации работы с арбитражными делами. Каждый модуль отвечает за определенную функциональность и может использоваться как независимо, так и в составе основного приложения.

## Основные модули

### 1. main.py - Главное меню

**Описание**: Точка входа в приложение с интерактивным меню.

**Функции**:
- `main()` - Запуск главного меню приложения
- `check_resume_option(filename: str) -> bool` - Проверка возможности возобновления процесса

**Использование**:
```python
python main.py
```

### 2. parser.py - Парсинг kad.arbitr.ru

**Описание**: Модуль для парсинга событий по делам с сайта kad.arbitr.ru.

**Основные функции**:

#### `get_case_events(driver: uc.Chrome, case_number: str) -> Tuple[Optional[Dict[str, Any]], int]`

Получает события для конкретного дела.

**Параметры**:
- `driver` - Chrome драйвер
- `case_number` - Номер дела

**Возвращает**:
- `Tuple[Optional[Dict[str, Any]], int]` - (данные события, количество событий)

**Пример**:
```python
from parser import get_case_events, get_driver

driver = get_driver()
event_data, events_count = get_case_events(driver, "А32-29491/2023")
```

#### `sync_chronology(batch_size: int = 50, pause_between_batches: int = 120, resume: bool = False) -> None`

Синхронизирует хронологию дел с базой данных.

**Параметры**:
- `batch_size` - Размер пакета дел (по умолчанию 50)
- `pause_between_batches` - Пауза между пакетами в секундах (по умолчанию 120)
- `resume` - Возобновление с последнего обработанного дела (по умолчанию False)

**Пример**:
```python
from parser import sync_chronology

# Обычный запуск
sync_chronology()

# С возобновлением
sync_chronology(resume=True)

# С настройками
sync_chronology(batch_size=25, pause_between_batches=60)
```

### 3. download_documents.py - Скачивание документов

**Описание**: Модуль для скачивания документов и выполнения OCR.

**Основные функции**:

#### `download_document(driver, url: str, case_number: str, event_title: str, event_date: str, case_participants=None, output_dir: str = "/Users/nikita/Dev/KadBot/documents") -> Optional[str]`

Скачивает документ по ссылке и выполняет OCR.

**Параметры**:
- `driver` - Chrome драйвер
- `url` - Ссылка на документ
- `case_number` - Номер дела
- `event_title` - Название события
- `event_date` - Дата события
- `case_participants` - Участники дела (опционально)
- `output_dir` - Папка для сохранения (по умолчанию "/Users/nikita/Dev/KadBot/documents")

**Возвращает**:
- `Optional[str]` - Путь к сохраненному файлу или None при ошибке

#### `download_documents(batch_size: int = 10, pause_between_batches: int = 30, resume: bool = False) -> None`

Скачивает документы по ссылкам из базы данных.

**Параметры**:
- `batch_size` - Размер пакета документов (по умолчанию 10)
- `pause_between_batches` - Пауза между пакетами в секундах (по умолчанию 30)
- `resume` - Возобновление с последнего документа (по умолчанию False)

**Пример**:
```python
from download_documents import download_documents

# Обычный запуск
download_documents()

# С возобновлением
download_documents(resume=True)

# С настройками
download_documents(batch_size=5, pause_between_batches=60)
```

### 4. crm_sync.py - Синхронизация с CRM

**Описание**: Модуль для синхронизации проектов из Aspro.Cloud.

**Основные функции**:

#### `get_projects() -> List[Dict[str, Any]]`

Получает список всех проектов из Aspro.Cloud через API.

**Возвращает**:
- `List[Dict[str, Any]]` - Список проектов с их данными

#### `extract_case_number(name: str) -> Optional[str]`

Извлекает номер дела из названия проекта.

**Параметры**:
- `name` - Название проекта

**Возвращает**:
- `Optional[str]` - Номер дела или None, если не найден

#### `sync_crm_projects_to_db() -> None`

Синхронизирует проекты из CRM с базой данных.

**Пример**:
```python
from crm_sync import sync_crm_projects_to_db

sync_crm_projects_to_db()
```

### 5. crm_notify.py - Уведомления в CRM

**Описание**: Модуль для отправки уведомлений в Aspro.Cloud.

**Основные функции**:

#### `send_case_update_comment(project_id: int, event_title: str, event_date: str, doc_link: Optional[str] = None) -> Optional[dict]`

Отправляет комментарий-уведомление об обновлении события по делу в проект Aspro.Cloud.

**Параметры**:
- `project_id` - ID проекта в CRM
- `event_title` - Название события
- `event_date` - Дата события
- `doc_link` - Ссылка на документ (опционально)

**Возвращает**:
- `Optional[dict]` - Ответ API при успешной отправке, None при ошибке

**Пример**:
```python
from crm_notify import send_case_update_comment

result = send_case_update_comment(
    project_id=123,
    event_title="Определение о принятии искового заявления",
    event_date="15.01.2024",
    doc_link="https://kad.arbitr.ru/document/123"
)
```

### 6. db.py - Работа с базой данных

**Описание**: Модуль для работы с базой данных SQLAlchemy.

**Основные функции**:

#### `get_project_id_for_case(case_number: str) -> Optional[int]`

Получает project_id для указанного номера дела из базы данных.

**Параметры**:
- `case_number` - Номер дела

**Возвращает**:
- `Optional[int]` - ID проекта в CRM или None, если дело не найдено

**Пример**:
```python
from db import get_project_id_for_case

project_id = get_project_id_for_case("А32-29491/2023")
```

### 7. models.py - Модели данных

**Описание**: SQLAlchemy модели для работы с базой данных.

**Модели**:

#### `Cases`
```python
class Cases(Base):
    __tablename__ = "cases"
    id = Column(Integer, primary_key=True)
    case_number = Column(String, unique=True, nullable=False)
    project_id = Column(Integer, unique=True, index=True)
```

#### `Chronology`
```python
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
```

### 8. utils.py - Утилиты

**Описание**: Общие утилиты для парсинга и скачивания документов.

**Основные функции**:

#### `get_driver(retries: int = 3, timeout: int = 30) -> Optional[uc.Chrome]`

Инициализирует и настраивает Chrome драйвер для парсинга.

**Параметры**:
- `retries` - Количество попыток инициализации драйвера (по умолчанию 3)
- `timeout` - Таймаут для сетевых операций (по умолчанию 30)

**Возвращает**:
- `Optional[uc.Chrome]` - Настроенный Chrome драйвер или None при ошибке

#### `save_progress(case_number: str, index: int, filename: str) -> None`

Сохраняет прогресс обработки в JSON-файл.

#### `load_progress(filename: str) -> Optional[Dict[str, Any]]`

Загружает прогресс обработки из JSON-файла.

#### `clear_progress(filename: str) -> None`

Удаляет файл прогресса.

#### `simulate_mouse_movement(driver: uc.Chrome) -> None`

Эмулирует движение мыши для имитации человеческого поведения.

**Пример**:
```python
from utils import get_driver, save_progress, load_progress

driver = get_driver()
save_progress("А32-29491/2023", 42, "parser_progress.json")
progress = load_progress("parser_progress.json")
```

### 9. logic.py - Бизнес-логика

**Описание**: Модуль с основной логикой парсинга и обработки дел.

**Основные функции**:

#### `parse_all_cases() -> None`

Парсит все дела из базы данных.

#### `parse_and_save_case(session, driver, case_number: str) -> None`

Парсит и сохраняет события для конкретного дела.

#### `notify_case_update(case_number: str, event_data: Dict[str, Any]) -> None`

Отправляет уведомление об обновлении дела в CRM.

### 10. init_db.py - Инициализация БД

**Описание**: Модуль для инициализации базы данных.

**Функции**:
- `init_db() -> None` - Создает все таблицы в базе данных

### 11. migrate_db.py - Миграции БД

**Описание**: Модуль для миграции базы данных.

**Функции**:
- `migrate_db() -> None` - Выполняет миграцию базы данных

### 12. test_notify.py - Тестирование уведомлений

**Описание**: Модуль для отправки тестового комментария в Aspro.Cloud.

**Функции**:
- `send_test_comment(entity_id: int, event_title: str, event_date: str, doc_link: Optional[str] = None) -> Optional[dict]` - Отправляет тестовый комментарий

## Переменные окружения

Создайте файл `.env` в корне проекта:

```env
# API ключи Aspro.Cloud
ASPRO_API_KEY=ваш_api_ключ
ASPRO_COMPANY=название_компании

# Пользователь для уведомлений
USERID=id_пользователя_в_crm
USER_NAME=Имя_Пользователя
```

## Обработка ошибок

Все модули используют стандартную обработку ошибок Python с логированием в файл `kad_parser.log`. При возникновении ошибок:

1. Проверьте логи: `tail -f kad_parser.log`
2. Убедитесь в корректности переменных окружения
3. Проверьте доступность сайтов kad.arbitr.ru и Aspro.Cloud
4. Убедитесь в установке всех зависимостей

## Возобновление процессов

Модули `parser.py` и `download_documents.py` поддерживают возобновление прерванных процессов:

```python
# Парсинг с возобновлением
from parser import sync_chronology
sync_chronology(resume=True)

# Скачивание документов с возобновлением
from download_documents import download_documents
download_documents(resume=True)
```

Прогресс сохраняется в файлы:
- `parser_progress.json` - для парсинга
- `download_progress.json` - для скачивания документов

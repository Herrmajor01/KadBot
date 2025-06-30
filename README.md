# KadBot 🤖

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

**KadBot** — это автоматизированный сервис на Python для синхронизации судебных дел из CRM (Aspro.Cloud), отслеживания новых событий с сайта [kad.arbitr.ru](https://kad.arbitr.ru) и скачивания документов.

## 🚀 Возможности

- **🔄 Синхронизация CRM**: Автоматическое получение неархивных проектов из Aspro.Cloud через API
- **📋 Извлечение дел**: Автоматическое извлечение номеров арбитражных дел из названий проектов
- **💾 Локальная БД**: Сохранение актуальных дел в SQLite с использованием SQLAlchemy ORM
- **🗑️ Управление архивом**: Автоматическое удаление архивных дел из базы данных
- **🔍 Парсинг событий**: Отслеживание новых событий по делам на kad.arbitr.ru
- **📄 Скачивание документов**: Автоматическое скачивание документов по ссылкам из базы данных
- **🔤 OCR обработка**: Извлечение текста из PDF документов с помощью Tesseract
- **📢 Уведомления**: Отправка уведомлений о новых событиях в CRM
- **⚡ Масштабируемость**: Поддержка сотен и тысяч дел с пагинацией
- **🛡️ Антиблокировка**: Использование undetected-chromedriver для обхода блокировок
- **🔄 Возобновление**: Поддержка возобновления прерванных процессов

## 📋 Требования

- Python 3.8+
- Google Chrome
- Tesseract OCR (для извлечения текста из документов)
- Доступ к API Aspro.Cloud
- Аккаунт на kad.arbitr.ru

## 🛠️ Установка

### 1. Клонирование репозитория

```bash
git clone <repository-url>
cd KadBot
```

### 2. Создание виртуального окружения

```bash
python3 -m venv venv
source venv/bin/activate  # Linux/macOS
# или
venv\Scripts\activate     # Windows
```

### 3. Установка зависимостей

#### Для продакшена:
```bash
pip install -r requirements.txt
```

#### Для разработки:
```bash
pip install -r requirements.txt
pip install -r requirements-dev.txt
pre-commit install
```

### 4. Установка Tesseract OCR

#### Ubuntu/Debian:
```bash
sudo apt-get install tesseract-ocr tesseract-ocr-rus
```

#### macOS:
```bash
brew install tesseract tesseract-lang
```

#### Windows:
Скачайте с [GitHub](https://github.com/UB-Mannheim/tesseract/wiki)

### 5. Настройка переменных окружения

Создайте файл `.env` в корне проекта:

```env
# API ключи Aspro.Cloud
ASPRO_API_KEY=ваш_api_ключ
ASPRO_COMPANY=название_компании

# Пользователь для уведомлений
USERID=id_пользователя_в_crm
USER_NAME=Имя_Пользователя
```

### 6. Инициализация базы данных

```bash
python init_db.py
```

## 🚀 Быстрый старт

### Использование Makefile (рекомендуется)

```bash
# Полная настройка для разработки
make dev-setup

# Запуск приложения
make run

# Синхронизация с CRM
make sync-crm

# Парсинг дел
make parse-cases

# Скачивание документов
make download-docs

# Отправка тестового уведомления
make test-notify
```

### Прямое использование Python

```bash
# Запуск основного меню
python main.py

# Инициализация БД
python init_db.py

# Миграция БД
python migrate_db.py

# Тестовое уведомление
python test_notify.py
```

## 📖 Использование

### Основное меню

При запуске `python main.py` вы увидите меню:

```
1. Синхронизировать CRM проекты
2. Парсить события по делам
3. Скачать документы по ссылкам из базы данных
```

### Синхронизация CRM

Выберите опцию **1** для синхронизации проектов из CRM:

- Загружает все неархивные проекты из Aspro.Cloud
- Извлекает номера дел из названий проектов
- Добавляет новые дела в базу данных
- Удаляет архивные дела из базы

### Парсинг событий

Выберите опцию **2** для парсинга событий:

- Обрабатывает все дела из базы данных
- Получает последние события с kad.arbitr.ru
- Сравнивает с сохраненными событиями
- Отправляет уведомления о новых событиях в CRM
- Поддерживает возобновление прерванного процесса

### Скачивание документов

Выберите опцию **3** для скачивания документов:

- Скачивает документы по ссылкам из базы данных
- Сохраняет PDF файлы в папку `documents/`
- Выполняет OCR для извлечения текста
- Создает текстовые файлы с содержимым документов
- Поддерживает возобновление прерванного процесса

## 🏗️ Архитектура

### Структура проекта

```
KadBot/
├── main.py              # Главное меню приложения
├── parser.py            # Основной парсер kad.arbitr.ru
├── download_documents.py # Скачивание документов и OCR
├── crm_sync.py          # Синхронизация с Aspro.Cloud
├── crm_notify.py        # Отправка уведомлений в CRM
├── db.py                # Настройки базы данных
├── models.py            # SQLAlchemy модели
├── logic.py             # Бизнес-логика
├── utils.py             # Утилиты (драйвер, прогресс)
├── init_db.py           # Инициализация БД
├── migrate_db.py        # Миграции БД
├── test_notify.py       # Тестирование уведомлений
├── documents/           # Папка для скачанных документов
├── requirements.txt     # Зависимости
├── requirements-dev.txt # Зависимости для разработки
├── setup.cfg            # Конфигурация инструментов
├── pyproject.toml       # Метаданные проекта
├── Makefile             # Команды для разработки
└── .pre-commit-config.yaml # Pre-commit хуки
```

### Модели данных

#### Cases
```python
class Cases(Base):
    __tablename__ = "cases"
    id = Column(Integer, primary_key=True)
    case_number = Column(String, unique=True, nullable=False)
    project_id = Column(Integer, unique=True, index=True)
```

#### Chronology
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

## 🔧 Разработка

### Установка инструментов разработки

```bash
make install-dev
```

### Форматирование кода

```bash
make format
```

### Проверка линтерами

```bash
make lint
```

### Запуск тестов

```bash
make test
```

### Полная проверка кода

```bash
make check-all
```

### Очистка временных файлов

```bash
make clean
```

## 🧪 Тестирование

### Структура тестов

```
tests/
├── test_parser.py
├── test_download_documents.py
├── test_crm_sync.py
├── test_crm_notify.py
├── test_db.py
└── conftest.py
```

### Запуск тестов

```bash
# Все тесты
pytest

# С покрытием
pytest --cov=. --cov-report=html

# Конкретный тест
pytest tests/test_parser.py::test_get_case_events
```

## 📊 Мониторинг

### Логи

Все действия записываются в файл `kad_parser.log`:

```bash
# Просмотр логов в реальном времени
tail -f kad_parser.log

# Поиск ошибок
grep "ERROR" kad_parser.log
```

### База данных

```bash
# Просмотр структуры БД
sqlite3 kad_cases.db ".schema"

# Количество дел
sqlite3 kad_cases.db "SELECT COUNT(*) FROM cases;"

# Последние события
sqlite3 kad_cases.db "SELECT * FROM chronology ORDER BY id DESC LIMIT 10;"
```

### Документы

```bash
# Просмотр скачанных документов
ls -la documents/

# Поиск документов по номеру дела
find documents/ -name "*А32-29491_2023*"
```

## ⚠️ Важные замечания

### Безопасность

- **API ключи**: Никогда не коммитьте файл `.env` в репозиторий
- **Блокировки**: Используйте разумные задержки между запросами
- **Документы**: Скачанные документы содержат конфиденциальную информацию

### Производительность

- **Пакетная обработка**: Дела обрабатываются пакетами по 50 штук
- **Паузы**: Между пакетами делается пауза 2-5 минут
- **Повторные попытки**: При ошибках делается до 3 попыток
- **OCR**: Обработка документов может занять значительное время

### Ограничения

- **Chrome**: Требуется установленный Google Chrome
- **Tesseract**: Требуется установленный Tesseract OCR
- **Сеть**: Стабильное интернет-соединение
- **Права**: Доступ к API Aspro.Cloud
- **Диск**: Место для хранения документов

## 🐛 Устранение неполадок

### Частые проблемы

#### Ошибка "Chrome driver not found"
```bash
# Установите Chrome
# Ubuntu/Debian
sudo apt-get install google-chrome-stable

# macOS
brew install --cask google-chrome

# Windows
# Скачайте с https://www.google.com/chrome/
```

#### Ошибка "Tesseract not found"
```bash
# Ubuntu/Debian
sudo apt-get install tesseract-ocr tesseract-ocr-rus

# macOS
brew install tesseract tesseract-lang

# Windows
# Скачайте с https://github.com/UB-Mannheim/tesseract/wiki
```

#### Ошибка "API key invalid"
```bash
# Проверьте файл .env
cat .env

# Убедитесь, что ключ правильный
# Проверьте права доступа к API
```

#### Ошибка "IP заблокирован"
```bash
# Увеличьте задержки в parser.py
time.sleep(random.uniform(10.0, 20.0))

# Используйте VPN
# Смените IP адрес
```

### Отладка

```bash
# Включение отладочных логов
export PYTHONPATH=.
python -c "
import logging
logging.basicConfig(level=logging.DEBUG)
from parser import get_driver
driver = get_driver()
"
```

## 🤝 Вклад в проект

### Установка pre-commit хуков

```bash
pre-commit install
```

### Процесс разработки

1. Создайте ветку для новой функции
2. Внесите изменения
3. Запустите проверки: `make check-all`
4. Создайте pull request

### Стандарты кода

- **Форматирование**: Black с длиной строки 79 символов
- **Импорты**: isort с профилем black
- **Линтинг**: flake8 + pylint
- **Типизация**: mypy
- **Докстринги**: Google style на русском языке

---

**KadBot** — автоматизация мониторинга арбитражных дел 🏛️

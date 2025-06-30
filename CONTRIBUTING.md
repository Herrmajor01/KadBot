# Руководство по участию в разработке KadBot

Спасибо за интерес к проекту KadBot! Мы приветствуем вклад от сообщества.

## Как внести свой вклад

### 1. Сообщить об ошибке

Если вы нашли ошибку, создайте issue с подробным описанием:

- **Краткое описание** проблемы
- **Шаги для воспроизведения** ошибки
- **Ожидаемое поведение**
- **Фактическое поведение**
- **Версия** Python, ОС, зависимостей
- **Логи** (если применимо)

### 2. Предложить новую функцию

Создайте issue с описанием новой функции:

- **Название** и краткое описание
- **Обоснование** необходимости
- **Предлагаемая реализация** (если есть идеи)
- **Примеры использования**

### 3. Внести изменения в код

#### Подготовка окружения

1. **Форкните** репозиторий
2. **Клонируйте** ваш форк:
   ```bash
   git clone https://github.com/your-username/KadBot.git
   cd KadBot
   ```

3. **Создайте** виртуальное окружение:
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # Linux/macOS
   # или
   venv\Scripts\activate     # Windows
   ```

4. **Установите** зависимости:
   ```bash
   pip install -r requirements.txt
   pip install -r requirements-dev.txt
   ```

5. **Настройте** pre-commit хуки:
   ```bash
   pre-commit install
   ```

#### Создание ветки

```bash
git checkout -b feature/your-feature-name
# или
git checkout -b fix/your-bug-fix
```

#### Разработка

1. **Следуйте** стандартам кода (см. ниже)
2. **Добавляйте** тесты для новых функций
3. **Обновляйте** документацию при необходимости
4. **Коммитьте** изменения с понятными сообщениями

#### Тестирование

```bash
# Запуск всех тестов
make test

# Проверка стиля кода
make check-all

# Запуск конкретного теста
pytest tests/test_parser.py::test_get_case_events
```

#### Создание Pull Request

1. **Отправьте** изменения в ваш форк:
   ```bash
   git push origin feature/your-feature-name
   ```

2. **Создайте** Pull Request в основном репозитории

3. **Опишите** изменения в PR:
   - Что изменилось
   - Почему это нужно
   - Как тестировать

## Стандарты кода

### Python код

- **Python 3.8+** совместимость
- **PEP 8** стиль кода
- **Type hints** для всех функций
- **Docstrings** на русском языке (Google style)
- **Максимальная длина строки**: 79 символов

### Форматирование

```bash
# Автоматическое форматирование
make format

# Проверка стиля
make lint
```

### Импорты

```python
# Стандартная библиотека
import os
import sys
from typing import Optional, List, Dict

# Сторонние библиотеки
import requests
from sqlalchemy import create_engine

# Локальные модули
from models import Cases
from utils import get_driver
```

### Документация

```python
def get_case_events(
    driver: uc.Chrome,
    case_number: str
) -> Tuple[Optional[Dict[str, Any]], int]:
    """Получает события для конкретного дела.

    Args:
        driver: Chrome драйвер для парсинга
        case_number: Номер дела для поиска

    Returns:
        Tuple[Optional[Dict[str, Any]], int]:
            (данные события, количество событий)

    Raises:
        WebDriverException: При ошибках браузера
        TimeoutException: При превышении времени ожидания
    """
    pass
```

### Тестирование

```python
def test_get_case_events():
    """Тест получения событий по делу."""
    # Arrange
    driver = get_driver()
    case_number = "А32-29491/2023"

    # Act
    event_data, events_count = get_case_events(driver, case_number)

    # Assert
    assert events_count >= 0
    if event_data:
        assert "event_date" in event_data
        assert "event_title" in event_data
```

## Структура проекта

```
KadBot/
├── main.py              # Главное меню
├── parser.py            # Парсинг kad.arbitr.ru
├── download_documents.py # Скачивание документов
├── crm_sync.py          # Синхронизация с CRM
├── crm_notify.py        # Уведомления в CRM
├── db.py                # Работа с БД
├── models.py            # SQLAlchemy модели
├── logic.py             # Бизнес-логика
├── utils.py             # Утилиты
├── init_db.py           # Инициализация БД
├── migrate_db.py        # Миграции БД
├── test_notify.py       # Тестирование уведомлений
├── tests/               # Тесты
├── documents/           # Скачанные документы
├── requirements.txt     # Зависимости
├── requirements-dev.txt # Зависимости для разработки
├── setup.cfg            # Конфигурация инструментов
├── pyproject.toml       # Метаданные проекта
├── Makefile             # Команды для разработки
├── README.md            # Основная документация
├── API.md               # Документация API
├── DEPLOYMENT.md        # Инструкции по развертыванию
├── CONTRIBUTING.md      # Это руководство
├── CHANGELOG.md         # История изменений
├── LICENSE              # Лицензия
└── env.example          # Пример переменных окружения
```

## Процесс ревью

### Критерии принятия

- [ ] Код соответствует стандартам проекта
- [ ] Все тесты проходят
- [ ] Добавлены тесты для новых функций
- [ ] Обновлена документация
- [ ] Код прошел проверку линтерами
- [ ] Нет конфликтов с основной веткой

### Комментарии в коде

```python
# Хорошо: объясняет сложную логику
if new_date > old_date or not old_date:
    # Обновляем событие только если новая дата более свежая
    # или если у нас еще нет сохраненной даты
    update_event()

# Плохо: очевидные комментарии
x = x + 1  # увеличиваем x на 1
```

## Коммиты

### Сообщения коммитов

Используйте [Conventional Commits](https://www.conventionalcommits.org/):

```
feat: добавить поддержку PostgreSQL
fix: исправить ошибку парсинга дат
docs: обновить README
test: добавить тесты для download_documents
refactor: переписать логику синхронизации
style: исправить форматирование кода
```

### Примеры

```bash
git commit -m "feat: добавить функцию скачивания документов

- Добавлен модуль download_documents.py
- Реализовано скачивание PDF файлов
- Добавлена OCR обработка с Tesseract
- Поддержка возобновления прерванных процессов

Closes #123"
```

## Вопросы и поддержка

### Получение помощи

- **Issues**: Для багов и предложений функций
- **Discussions**: Для вопросов и обсуждений
- **Wiki**: Для дополнительной документации

### Связаться с командой

- **Email**: [ваш-email@example.com]
- **Telegram**: [@username]
- **Discord**: [ссылка на сервер]

## Лицензия

Участвуя в проекте, вы соглашаетесь с тем, что ваш вклад будет лицензирован под MIT License.

## Благодарности

Спасибо всем участникам, которые помогают развивать KadBot!

---

**Примечание**: Это руководство может обновляться. Следите за изменениями в репозитории.

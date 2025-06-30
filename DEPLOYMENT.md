# Инструкции по развертыванию KadBot

## Системные требования

### Минимальные требования
- **ОС**: Linux (Ubuntu 20.04+), macOS 10.15+, Windows 10+
- **Python**: 3.8 или выше
- **RAM**: 4 GB
- **Диск**: 10 GB свободного места
- **Сеть**: Стабильное интернет-соединение

### Рекомендуемые требования
- **ОС**: Ubuntu 22.04 LTS
- **Python**: 3.11
- **RAM**: 8 GB
- **Диск**: 50 GB свободного места
- **Сеть**: Высокоскоростное интернет-соединение

## Установка на Ubuntu/Debian

### 1. Обновление системы
```bash
sudo apt update && sudo apt upgrade -y
```

### 2. Установка Python и pip
```bash
sudo apt install python3 python3-pip python3-venv -y
```

### 3. Установка Google Chrome
```bash
wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | sudo apt-key add -
echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" | sudo tee /etc/apt/sources.list.d/google-chrome.list
sudo apt update
sudo apt install google-chrome-stable -y
```

### 4. Установка Tesseract OCR
```bash
sudo apt install tesseract-ocr tesseract-ocr-rus -y
```

### 5. Установка дополнительных зависимостей
```bash
sudo apt install poppler-utils -y  # для работы с PDF
```

### 6. Клонирование проекта
```bash
git clone <repository-url>
cd KadBot
```

### 7. Создание виртуального окружения
```bash
python3 -m venv venv
source venv/bin/activate
```

### 8. Установка зависимостей
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 9. Настройка переменных окружения
```bash
cp .env.example .env
nano .env
```

### 10. Инициализация базы данных
```bash
python init_db.py
```

## Установка на macOS

### 1. Установка Homebrew (если не установлен)
```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

### 2. Установка Python
```bash
brew install python@3.11
```

### 3. Установка Google Chrome
```bash
brew install --cask google-chrome
```

### 4. Установка Tesseract OCR
```bash
brew install tesseract tesseract-lang
```

### 5. Установка дополнительных зависимостей
```bash
brew install poppler
```

### 6. Клонирование и настройка проекта
```bash
git clone <repository-url>
cd KadBot
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
cp .env.example .env
nano .env
python init_db.py
```

## Установка на Windows

### 1. Установка Python
Скачайте и установите Python 3.11 с [python.org](https://www.python.org/downloads/)

### 2. Установка Google Chrome
Скачайте и установите Chrome с [google.com/chrome](https://www.google.com/chrome/)

### 3. Установка Tesseract OCR
1. Скачайте установщик с [GitHub](https://github.com/UB-Mannheim/tesseract/wiki)
2. Установите Tesseract, добавив его в PATH
3. Установите русский языковой пакет

### 4. Клонирование и настройка проекта
```cmd
git clone <repository-url>
cd KadBot
python -m venv venv
venv\Scripts\activate
pip install --upgrade pip
pip install -r requirements.txt
copy .env.example .env
notepad .env
python init_db.py
```

## Настройка переменных окружения

Создайте файл `.env` в корне проекта:

```env
# API ключи Aspro.Cloud
ASPRO_API_KEY=ваш_api_ключ_здесь
ASPRO_COMPANY=название_вашей_компании

# Пользователь для уведомлений
USERID=id_пользователя_в_crm
USER_NAME=Имя_Пользователя

# Настройки путей (опционально)
DOCUMENTS_DIR=/path/to/documents
LOG_LEVEL=INFO
```

### Получение API ключа Aspro.Cloud

1. Войдите в ваш аккаунт Aspro.Cloud
2. Перейдите в настройки → API
3. Создайте новый API ключ
4. Скопируйте ключ в переменную `ASPRO_API_KEY`

### Получение ID пользователя

1. Войдите в ваш аккаунт Aspro.Cloud
2. Перейдите в профиль пользователя
3. Скопируйте ID пользователя в переменную `USERID`

## Проверка установки

### 1. Тест Chrome драйвера
```bash
python -c "
from utils import get_driver
driver = get_driver()
if driver:
    print('Chrome драйвер работает корректно')
    driver.quit()
else:
    print('Ошибка инициализации Chrome драйвера')
"
```

### 2. Тест Tesseract OCR
```bash
tesseract --version
```

### 3. Тест подключения к CRM
```bash
python test_notify.py
```

### 4. Запуск основного приложения
```bash
python main.py
```

## Настройка автоматического запуска

### Создание systemd сервиса (Linux)

Создайте файл `/etc/systemd/system/kadbot.service`:

```ini
[Unit]
Description=KadBot - Парсер арбитражных дел
After=network.target

[Service]
Type=simple
User=your_username
WorkingDirectory=/path/to/KadBot
Environment=PATH=/path/to/KadBot/venv/bin
ExecStart=/path/to/KadBot/venv/bin/python main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Активируйте сервис:
```bash
sudo systemctl daemon-reload
sudo systemctl enable kadbot
sudo systemctl start kadbot
```

### Создание cron задачи

Добавьте в crontab (`crontab -e`):

```bash
# Запуск парсинга каждый час
0 * * * * cd /path/to/KadBot && /path/to/KadBot/venv/bin/python -c "from parser import sync_chronology; sync_chronology()"

# Скачивание документов каждые 6 часов
0 */6 * * * cd /path/to/KadBot && /path/to/KadBot/venv/bin/python -c "from download_documents import download_documents; download_documents()"
```

## Мониторинг и логирование

### Настройка ротации логов

Создайте файл `/etc/logrotate.d/kadbot`:

```
/path/to/KadBot/kad_parser.log {
    daily
    rotate 30
    compress
    delaycompress
    missingok
    notifempty
    create 644 your_username your_username
}
```

### Мониторинг через journalctl (systemd)

```bash
# Просмотр логов сервиса
sudo journalctl -u kadbot -f

# Просмотр ошибок
sudo journalctl -u kadbot -p err
```

## Резервное копирование

### Автоматическое резервное копирование БД

Создайте скрипт `/path/to/KadBot/backup.sh`:

```bash
#!/bin/bash
BACKUP_DIR="/path/to/backups"
DATE=$(date +%Y%m%d_%H%M%S)
DB_FILE="/path/to/KadBot/kad_cases.db"

mkdir -p $BACKUP_DIR
cp $DB_FILE $BACKUP_DIR/kad_cases_$DATE.db
gzip $BACKUP_DIR/kad_cases_$DATE.db

# Удаление старых резервных копий (старше 30 дней)
find $BACKUP_DIR -name "kad_cases_*.db.gz" -mtime +30 -delete
```

Сделайте скрипт исполняемым и добавьте в cron:
```bash
chmod +x /path/to/KadBot/backup.sh
# Добавьте в crontab: 0 2 * * * /path/to/KadBot/backup.sh
```

## Обновление

### Обновление кода
```bash
cd /path/to/KadBot
git pull origin main
source venv/bin/activate
pip install -r requirements.txt
python migrate_db.py
```

### Обновление зависимостей
```bash
source venv/bin/activate
pip install --upgrade -r requirements.txt
```

## Устранение неполадок

### Проблемы с Chrome драйвером

```bash
# Проверка версии Chrome
google-chrome --version

# Переустановка Chrome драйвера
pip uninstall undetected-chromedriver
pip install undetected-chromedriver
```

### Проблемы с Tesseract

```bash
# Проверка установки Tesseract
tesseract --version

# Проверка языковых пакетов
tesseract --list-langs
```

### Проблемы с правами доступа

```bash
# Установка правильных прав на папки
chmod 755 /path/to/KadBot
chmod 644 /path/to/KadBot/*.py
chmod 600 /path/to/KadBot/.env
```

### Проблемы с сетью

```bash
# Проверка доступности сайтов
curl -I https://kad.arbitr.ru
curl -I https://aspro.cloud
```

## Безопасность

### Рекомендации по безопасности

1. **Ограничение доступа к файлам**:
   ```bash
   chmod 600 .env
   chmod 644 *.py
   ```

2. **Использование отдельного пользователя**:
   ```bash
   sudo useradd -r -s /bin/false kadbot
   sudo chown -R kadbot:kadbot /path/to/KadBot
   ```

3. **Настройка файрвола**:
   ```bash
   sudo ufw allow ssh
   sudo ufw enable
   ```

4. **Регулярное обновление системы**:
   ```bash
   sudo apt update && sudo apt upgrade -y
   ```

## Производительность

### Оптимизация для больших объемов данных

1. **Увеличение размера пакетов**:
   ```python
   sync_chronology(batch_size=100)
   download_documents(batch_size=20)
   ```

2. **Настройка пауз**:
   ```python
   sync_chronology(pause_between_batches=300)  # 5 минут
   download_documents(pause_between_batches=60)  # 1 минута
   ```

3. **Использование SSD дисков** для базы данных и документов

4. **Увеличение RAM** для обработки больших документов

## Поддержка

При возникновении проблем:

1. Проверьте логи: `tail -f kad_parser.log`
2. Убедитесь в корректности переменных окружения
3. Проверьте системные требования
4. Создайте issue в репозитории проекта

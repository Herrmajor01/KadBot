.PHONY: help install install-dev clean lint format test run setup-db migrate-db

help: ## Показать справку по командам
	@echo "Доступные команды:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install: ## Установить зависимости для продакшена
	pip install -r requirements.txt

install-dev: ## Установить зависимости для разработки
	pip install -r requirements.txt
	pip install -r requirements-dev.txt
	pre-commit install

clean: ## Очистить временные файлы
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type f -name "*.log" -delete
	find . -type f -name "error_*.html" -delete
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	rm -rf .pytest_cache/
	rm -rf htmlcov/
	rm -rf .coverage

lint: ## Проверить код с помощью линтеров
	flake8 *.py --max-line-length=79
	pylint *.py --disable=C0114,C0116

format: ## Отформатировать код
	black *.py --line-length=79
	isort *.py --profile=black

test: ## Запустить тесты
	pytest tests/ -v --cov=. --cov-report=html

run: ## Запустить основное приложение
	python main.py

setup-db: ## Инициализировать базу данных
	python init_db.py

migrate-db: ## Выполнить миграцию базы данных
	python migrate_db.py

sync-crm: ## Синхронизировать проекты из CRM
	python -c "from crm_sync import sync_crm_projects_to_db; sync_crm_projects_to_db()"

parse-cases: ## Запустить парсинг дел
	python -c "from parser import sync_chronology; sync_chronology()"

test-notify: ## Отправить тестовое уведомление
	python test_notify.py

check-all: format lint test ## Выполнить все проверки кода

dev-setup: install-dev setup-db ## Полная настройка для разработки
	@echo "Настройка завершена! Используйте 'make run' для запуска приложения."

.PHONY: help install install-dev clean lint format test run cli setup-db migrate-db sync-crm parse-cases download-docs check-all dev-setup

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
	flake8 kadbot *.py tests --max-line-length=79 --extend-ignore=F401
	pylint kadbot *.py --recursive=y --disable=C0114,C0116

format: ## Отформатировать код
	black kadbot *.py --line-length=79
	isort kadbot *.py --profile=black

test: ## Запустить тесты
	pytest tests/ -v --cov=. --cov-report=html

run: ## Запустить основное приложение
	python main.py

cli: ## Показать справку CLI (kadbot)
	python -m kadbot.cli -h

setup-db: ## Инициализировать базу данных
	python -m kadbot.db.init_db

migrate-db: ## Выполнить миграцию базы данных
	python -m kadbot.db.migrate

sync-crm: ## Синхронизировать проекты из CRM (CLI)
	python -m kadbot.cli sync

parse-cases: ## Запустить парсинг дел (CLI)
	python -m kadbot.cli parse

download-docs: ## Скачать документы и выполнить OCR (CLI)
	python -m kadbot.cli download --resume

# Устаревшие цели удалены: test-notify, run-calendar-api

check-all: format lint test ## Выполнить все проверки кода

dev-setup: install-dev setup-db ## Полная настройка для разработки
	@echo "Настройка завершена! Используйте 'make run' для запуска приложения."

.PHONY: help install docker-up docker-down migrate test lint format clean

help:
	@echo "DocCompare - Makefile commands:"
	@echo "  make install      - Установить зависимости"
	@echo "  make docker-up    - Запустить Docker инфраструктуру"
	@echo "  make docker-down  - Остановить Docker"
	@echo "  make migrate      - Применить миграции БД"
	@echo "  make test         - Запустить тесты"
	@echo "  make lint         - Проверить код"
	@echo "  make format       - Форматировать код"
	@echo "  make run          - Запустить сервер разработки"
	@echo "  make clean        - Очистить временные файлы"

install:
	pip install -r requirements.txt

docker-up:
	docker-compose up -d
	@echo "Ожидание готовности сервисов..."
	@sleep 10
	@echo "Инфраструктура запущена!"
	@echo "PostgreSQL: localhost:5432"
	@echo "Redis: localhost:6379"
	@echo "MinIO Console: http://localhost:9001"
	@echo "Grafana: http://localhost:3000 (admin/admin)"

docker-down:
	docker-compose down

migrate:
	alembic upgrade head

migrate-create:
	@read -p "Enter migration message: " msg; \
	alembic revision --autogenerate -m "$$msg"

test:
	pytest tests/ -v --cov=app --cov-report=html

lint:
	flake8 app/ tests/
	mypy app/

format:
	black app/ tests/
	isort app/ tests/

run:
	uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".mypy_cache" -exec rm -rf {} +
	rm -rf htmlcov/
	rm -rf .coverage

dev-setup: install docker-up
	@echo "Waiting for services..."
	@sleep 10
	@make migrate
	@echo "Development environment ready!"

all: install docker-up migrate test



# DocCompare - Система сравнения документов

Автоматическое сравнение версий офисных документов с выявлением семантических изменений.

## Описание

Система анализирует две версии документа (DOC, DOCX, PDF) и выявляет **смысловые изменения**, игнорируя косметические правки (форматирование, пунктуацию, перефразирование без изменения смысла).

## Возможности

- ✅ Поддержка форматов: DOC, DOCX, PDF (включая сканированные документы через OCR)
- ✅ Семантический анализ изменений с использованием LLM
- ✅ Классификация изменений по категориям (сроки, обязательства, финансы и т.д.)
- ✅ Оценка влияния изменений (низкое/среднее/высокое)
- ✅ Отчёты в форматах HTML, PDF, JSON
- ✅ REST API для интеграций
- ✅ Поддержка русского языка

## Архитектура

### Pipeline обработки

1. **Приём документов** - загрузка и идентификация файлов
2. **Извлечение текста** - парсинг DOC/DOCX/PDF + OCR для сканов
3. **Технический diff** - поиск различий на уровне текста
4. **Семантический анализ** - LLM-классификация изменений
5. **Формирование отчёта** - генерация HTML/PDF/JSON
6. **Хранение** - сохранение результатов и метаданных

### Технологический стек

- **Backend**: Python 3.11+, FastAPI
- **База данных**: PostgreSQL
- **Кэш/очереди**: Redis
- **Хранилище**: MinIO (S3-compatible)
- **LLM**: OpenAI API / Azure OpenAI / локальные модели
- **OCR**: Tesseract / Azure Document Intelligence
- **Парсинг документов**: python-docx, PyMuPDF, pdfminer.six
- **Контейнеризация**: Docker, Docker Compose

## Быстрый старт

### Требования

- Docker Desktop
- Python 3.11+
- API ключ для LLM (OpenAI или аналог)

### Установка

```bash
# Клонировать репозиторий
git clone https://github.com/travinov/DocCompare.git
cd DocCompare

# Настроить переменные окружения
cp .env.example .env
# Отредактировать .env и добавить API ключи

# Запустить инфраструктуру
docker-compose up -d

# Установить зависимости Python
pip install -r requirements.txt

# Применить миграции БД
alembic upgrade head

# Запустить сервер
uvicorn app.main:app --reload
```

### Использование API

```bash
# Загрузить документы для сравнения
curl -X POST http://localhost:8000/api/v1/compare \
  -F "base_file=@document_v1.docx" \
  -F "target_file=@document_v2.docx"

# Получить отчёт
curl http://localhost:8000/api/v1/reports/{case_id}
```

## Структура проекта

```
DocCompare/
├── app/
│   ├── api/              # REST API endpoints
│   ├── core/             # Конфигурация, настройки
│   ├── models/           # SQLAlchemy модели
│   ├── schemas/          # Pydantic схемы
│   ├── services/         # Бизнес-логика
│   │   ├── extraction/   # Извлечение текста
│   │   ├── diff/         # Diff-анализ
│   │   ├── llm/          # LLM-интеграция
│   │   └── reports/      # Генерация отчётов
│   ├── storage/          # Работа с S3/MinIO
│   └── main.py           # Точка входа FastAPI
├── tests/                # Тесты
├── docker/               # Dockerfile'ы
├── alembic/              # Миграции БД
├── docker-compose.yml    # Инфраструктура
├── requirements.txt      # Python зависимости
└── .env.example          # Пример конфигурации
```

## Разработка

### Запуск тестов

```bash
pytest tests/
```

### Мониторинг

- **Grafana**: http://localhost:3000
- **Prometheus**: http://localhost:9090

## Лицензия

MIT


# Сводка по проекту DocCompare

## 📊 Статистика

- **Всего Python файлов:** 29
- **Строк кода:** ~2,400
- **Коммитов:** 4
- **Файлов в репозитории:** 45+

## 🔗 Ссылки

- **GitHub репозиторий:** https://github.com/travinov/DocCompare
- **Клонирование:** `git clone https://github.com/travinov/DocCompare.git`

## 📂 Структура проекта

```
DocCompare/
├── app/                      # Основное приложение
│   ├── api/v1/              # REST API endpoints
│   ├── core/                # Конфигурация, БД, логирование
│   ├── models/              # SQLAlchemy модели
│   ├── schemas/             # Pydantic схемы
│   ├── services/            # Бизнес-логика
│   │   ├── extraction/      # Извлечение текста из документов
│   │   ├── diff/            # Diff-анализ
│   │   ├── llm/             # LLM семантический анализ
│   │   └── reports/         # Генерация отчётов
│   ├── storage/             # S3/MinIO клиент
│   └── main.py              # Точка входа FastAPI
│
├── tests/                   # Тесты
├── docker/                  # Конфигурация мониторинга
├── alembic/                 # Миграции БД
│
├── docker-compose.yml       # Docker инфраструктура
├── requirements.txt         # Python зависимости
├── Makefile                 # Команды для разработки
├── alembic.ini             # Конфигурация Alembic
├── pytest.ini              # Конфигурация тестов
│
├── README.md               # Основная документация
├── QUICKSTART.md           # Быстрый старт
├── DEPLOYMENT.md           # Руководство по развёртыванию
├── API_EXAMPLES.md         # Примеры использования API
├── CONTRIBUTING.md         # Руководство для контрибьюторов
├── LICENSE                 # MIT License
└── TZ_Document_Comparison.md  # Техническое задание
```

## ✅ Реализованные модули

### 1. Извлечение текста (`app/services/extraction/`)
- ✅ Поддержка DOCX через python-docx
- ✅ Поддержка PDF через PyMuPDF
- ✅ OCR для сканированных PDF (Tesseract)
- ✅ Нормализация и сегментация текста
- ✅ Определение структуры документа

### 2. Diff-анализ (`app/services/diff/`)
- ✅ Сравнение на уровне абзацев (difflib)
- ✅ Фильтрация шума (пробелы, регистр, пунктуация)
- ✅ Детальный diff на уровне слов (diff-match-patch)
- ✅ Оценка схожести текстов (rapidfuzz)
- ✅ Подсчёт статистики изменений

### 3. LLM семантический анализ (`app/services/llm/`)
- ✅ Интеграция с OpenAI GPT-4
- ✅ Классификация изменений (dates, financial, obligations, etc.)
- ✅ Оценка влияния (low, medium, high)
- ✅ Генерация сводок на русском языке
- ✅ Batch обработка для оптимизации
- ✅ Fallback режим без LLM

### 4. Генератор отчётов (`app/services/reports/`)
- ✅ HTML отчёты с красивой визуализацией
- ✅ PDF отчёты через WeasyPrint
- ✅ JSON отчёты для интеграций
- ✅ Группировка по категориям
- ✅ Статистика и графики

### 5. REST API (`app/api/v1/`)
- ✅ POST /api/v1/compare - загрузка документов
- ✅ GET /api/v1/compare/{id} - статус обработки
- ✅ GET /api/v1/compare/{id}/changes - список изменений
- ✅ GET /api/v1/compare/{id}/reports - ссылки на отчёты
- ✅ GET /api/v1/compare/{id}/report/html - HTML отчёт
- ✅ DELETE /api/v1/compare/{id} - удаление кейса
- ✅ Swagger UI документация
- ✅ Асинхронная обработка

### 6. Инфраструктура
- ✅ PostgreSQL для хранения данных
- ✅ Redis для кэширования и очередей
- ✅ MinIO (S3-compatible) для файлов
- ✅ Prometheus для метрик
- ✅ Grafana для визуализации
- ✅ Docker Compose для оркестрации

### 7. База данных
- ✅ SQLAlchemy модели
- ✅ Alembic миграции
- ✅ Async поддержка (asyncpg)
- ✅ Связанные таблицы (cases, documents, changes)

### 8. Дополнительно
- ✅ Структурированное логирование (structlog)
- ✅ Конфигурация через .env
- ✅ Prometheus метрики
- ✅ Тесты (pytest)
- ✅ Code formatting (black, isort)
- ✅ Type hints
- ✅ Полная документация

## 🚀 Быстрый старт

### Минимальные требования
- Docker Desktop
- Python 3.11+
- Tesseract OCR
- OpenAI API ключ

### Запуск за 5 минут

```bash
# 1. Клонировать
git clone https://github.com/travinov/DocCompare.git
cd DocCompare

# 2. Настроить окружение
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 3. Создать .env
cp .env.example .env
# Добавить OPENAI_API_KEY в .env

# 4. Запустить Docker
make docker-up

# 5. Создать БД
alembic revision --autogenerate -m "Initial"
alembic upgrade head

# 6. Запустить
make run
```

Открыть: http://localhost:8000/docs

## 📚 Документация

| Файл | Описание |
|------|----------|
| **README.md** | Обзор проекта, установка, возможности |
| **QUICKSTART.md** | Быстрый старт за 5 минут |
| **DEPLOYMENT.md** | Полное руководство по развёртыванию |
| **API_EXAMPLES.md** | Примеры использования API (curl, Python, JS) |
| **CONTRIBUTING.md** | Руководство для контрибьюторов |

## 🎯 Использование

### Пример 1: Через Swagger UI
1. Открыть http://localhost:8000/docs
2. POST /api/v1/compare - загрузить документы
3. GET /api/v1/compare/{id} - проверить статус
4. GET /api/v1/compare/{id}/report/html - получить отчёт

### Пример 2: Через Python
```python
import requests

# Загрузка документов
with open("v1.docx", "rb") as f1, open("v2.docx", "rb") as f2:
    response = requests.post(
        "http://localhost:8000/api/v1/compare",
        files={"base_file": f1, "target_file": f2}
    )

case_id = response.json()["id"]

# Получение результата
result = requests.get(f"http://localhost:8000/api/v1/compare/{case_id}")
print(f"Найдено изменений: {result.json()['total_changes']}")
```

## 🔧 Полезные команды

```bash
make help          # Показать все команды
make docker-up     # Запустить инфраструктуру
make migrate       # Применить миграции
make run           # Запустить сервер
make test          # Запустить тесты
make lint          # Проверить код
make format        # Форматировать код
make docker-down   # Остановить Docker
make clean         # Очистить временные файлы
```

## 📊 Сервисы

| Сервис | URL | Credentials |
|--------|-----|-------------|
| API | http://localhost:8000 | - |
| Swagger | http://localhost:8000/docs | - |
| PostgreSQL | localhost:5432 | doccompare/doccompare_pass |
| MinIO Console | http://localhost:9001 | minioadmin/minioadmin |
| Grafana | http://localhost:3000 | admin/admin |
| Prometheus | http://localhost:9090 | - |

## 🎨 Особенности

- 🚀 **Высокая производительность** - асинхронная обработка
- 🤖 **AI-powered** - использование GPT-4 для анализа
- 🎯 **Точность** - многоуровневый анализ (технический + семантический)
- 📊 **Красивые отчёты** - HTML с визуализацией
- 🐳 **Docker-ready** - вся инфраструктура в контейнерах
- 📈 **Мониторинг** - Prometheus + Grafana из коробки
- 🔒 **Безопасность** - валидация данных, изоляция
- 📝 **Документация** - Swagger UI + подробные гайды
- 🧪 **Тестируемость** - pytest + fixtures
- 🌍 **Масштабируемость** - готов к продакшену

## 🏆 Технологический стек

**Backend:**
- Python 3.11+
- FastAPI
- SQLAlchemy (async)
- Pydantic

**Обработка документов:**
- python-docx
- PyMuPDF
- Tesseract OCR
- pdf2image

**Анализ:**
- OpenAI GPT-4
- difflib
- rapidfuzz
- diff-match-patch

**Инфраструктура:**
- PostgreSQL 16
- Redis 7
- MinIO
- Docker Compose

**Мониторинг:**
- Prometheus
- Grafana
- structlog

**Отчёты:**
- Jinja2
- WeasyPrint
- BeautifulSoup

## 📝 Лицензия

MIT License - см. файл LICENSE

## 🤝 Контрибьюция

См. CONTRIBUTING.md для деталей

---

**Создано:** 21 октября 2025  
**Версия:** 1.0.0  
**Автор:** DocCompare Team  
**Репозиторий:** https://github.com/travinov/DocCompare


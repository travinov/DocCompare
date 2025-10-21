# 🚀 Быстрый старт DocCompare

## За 5 минут до первого запуска

### 1️⃣ Установка зависимостей

```bash
# Установить Tesseract OCR (для распознавания сканов)
# macOS:
brew install tesseract tesseract-lang

# Ubuntu/Linux:
# sudo apt-get install tesseract-ocr tesseract-ocr-rus tesseract-ocr-eng
```

### 2️⃣ Настройка проекта

```bash
# Создать виртуальное окружение
python3 -m venv venv
source venv/bin/activate

# Установить Python зависимости
pip install -r requirements.txt

# Создать файл конфигурации
cp .env.example .env
```

### 3️⃣ Настроить API ключ OpenAI

Отредактируйте `.env` и добавьте ваш API ключ:

```bash
OPENAI_API_KEY=sk-your-openai-api-key-here
```

Или используйте nano/vim:
```bash
nano .env
# Найти строку OPENAI_API_KEY и вставить ключ
```

### 4️⃣ Запустить инфраструктуру

```bash
# Запустить Docker контейнеры (PostgreSQL, Redis, MinIO, Prometheus, Grafana)
make docker-up

# Дождаться готовности сервисов (~10 секунд)
```

Проверить статус:
```bash
docker-compose ps
```

Все сервисы должны быть в статусе `Up`.

### 5️⃣ Создать таблицы БД

```bash
# Создать первую миграцию
alembic revision --autogenerate -m "Initial migration"

# Применить миграции
alembic upgrade head
```

### 6️⃣ Запустить сервер

```bash
# Запустить FastAPI сервер
make run

# Или напрямую:
# uvicorn app.main:app --reload
```

Сервер запустится на http://localhost:8000

### 7️⃣ Проверить работоспособность

Открыть в браузере:
- **API документация**: http://localhost:8000/docs
- **Swagger UI**: http://localhost:8000/docs
- **Health check**: http://localhost:8000/health

Или через curl:
```bash
curl http://localhost:8000/health
# Должно вернуть: {"status":"healthy"}
```

## 📝 Первое сравнение документов

### Через Swagger UI (в браузере)

1. Открыть http://localhost:8000/docs
2. Найти `POST /api/v1/compare`
3. Нажать "Try it out"
4. Загрузить два файла (base_file и target_file)
5. Нажать "Execute"
6. Скопировать `id` из ответа
7. Использовать `GET /api/v1/compare/{case_id}` для проверки статуса
8. Когда `status` станет `completed`, открыть отчёт:
   - `GET /api/v1/compare/{case_id}/report/html`

### Через curl

```bash
# Загрузить документы для сравнения
curl -X POST http://localhost:8000/api/v1/compare \
  -F "base_file=@/path/to/document_v1.docx" \
  -F "target_file=@/path/to/document_v2.docx"

# Скопировать case_id из ответа, например: 550e8400-e29b-41d4-a716-446655440000

# Проверить статус
curl http://localhost:8000/api/v1/compare/550e8400-e29b-41d4-a716-446655440000

# Когда status = completed, получить HTML отчёт
curl http://localhost:8000/api/v1/compare/550e8400-e29b-41d4-a716-446655440000/report/html > report.html

# Открыть отчёт в браузере
open report.html  # macOS
# xdg-open report.html  # Linux
```

### Через Python

```python
import requests
import time

# Загрузка документов
with open("document_v1.docx", "rb") as f1, open("document_v2.docx", "rb") as f2:
    response = requests.post(
        "http://localhost:8000/api/v1/compare",
        files={"base_file": f1, "target_file": f2}
    )

case_id = response.json()["id"]
print(f"Case ID: {case_id}")

# Ожидание завершения
while True:
    response = requests.get(f"http://localhost:8000/api/v1/compare/{case_id}")
    status = response.json()["status"]
    print(f"Status: {status}")
    
    if status == "completed":
        data = response.json()
        print(f"\nНайдено изменений: {data['total_changes']}")
        print(f"Семантических: {data['semantic_changes_count']}")
        print(f"Сводка: {data['summary']}")
        break
    
    time.sleep(2)

# Получить HTML отчёт
report = requests.get(f"http://localhost:8000/api/v1/compare/{case_id}/report/html")
with open("report.html", "wb") as f:
    f.write(report.content)
print("Отчёт сохранён в report.html")
```

## 🔍 Доступ к сервисам

После запуска `make docker-up` доступны следующие сервисы:

| Сервис | URL | Логин | Пароль |
|--------|-----|-------|--------|
| **API** | http://localhost:8000 | - | - |
| **Swagger UI** | http://localhost:8000/docs | - | - |
| **PostgreSQL** | localhost:5432 | doccompare | doccompare_pass |
| **Redis** | localhost:6379 | - | - |
| **MinIO Console** | http://localhost:9001 | minioadmin | minioadmin |
| **Grafana** | http://localhost:3000 | admin | admin |
| **Prometheus** | http://localhost:9090 | - | - |

## 🛠 Полезные команды

```bash
# Показать все команды
make help

# Запустить тесты
make test

# Проверить код (линтинг)
make lint

# Форматировать код
make format

# Остановить Docker контейнеры
make docker-down

# Полная очистка
make clean

# Посмотреть логи
docker-compose logs -f

# Логи конкретного сервиса
docker-compose logs -f postgres
docker-compose logs -f redis
docker-compose logs -f minio
```

## 📦 Что дальше?

1. **Изучить API**: http://localhost:8000/docs
2. **Посмотреть примеры**: См. `API_EXAMPLES.md`
3. **Развернуть на сервере**: См. `DEPLOYMENT.md`
4. **Настроить мониторинг**: Grafana на http://localhost:3000

## ❗ Типичные проблемы

### Проблема: Docker контейнеры не запускаются

```bash
# Проверить, что Docker Desktop запущен
docker ps

# Освободить порты, если заняты
lsof -i :5432  # PostgreSQL
lsof -i :6379  # Redis
lsof -i :9000  # MinIO

# Пересоздать контейнеры
docker-compose down -v
docker-compose up -d
```

### Проблема: Ошибка подключения к БД

```bash
# Убедиться, что PostgreSQL запущен
docker-compose ps postgres

# Проверить логи
docker-compose logs postgres

# Пересоздать БД
docker-compose down -v
docker-compose up -d postgres
sleep 10
alembic upgrade head
```

### Проблема: "ModuleNotFoundError"

```bash
# Активировать виртуальное окружение
source venv/bin/activate

# Переустановить зависимости
pip install -r requirements.txt
```

### Проблема: OCR не работает

```bash
# Проверить Tesseract
tesseract --version

# Проверить установленные языки
tesseract --list-langs

# Переустановить (macOS)
brew reinstall tesseract tesseract-lang
```

### Проблема: OpenAI API ключ не работает

1. Проверить, что ключ добавлен в `.env`:
   ```bash
   grep OPENAI_API_KEY .env
   ```

2. Проверить баланс: https://platform.openai.com/usage

3. Временно использовать fallback режим (без LLM):
   - Система будет работать с упрощённым анализом

## 💡 Советы

- **Используйте небольшие файлы для тестов** - первое сравнение может занять 30-60 секунд
- **Проверяйте логи** - `docker-compose logs -f` покажет что происходит
- **Мониторьте метрики** - Grafana поможет отследить производительность
- **Делайте бэкапы БД** - особенно перед обновлениями

## 🎯 Готовые тестовые документы

Для быстрого тестирования создайте два простых DOCX файла:

**document_v1.docx:**
```
Договор оказания услуг

1. Предмет договора
Исполнитель обязуется оказать услуги, а Заказчик - оплатить их.

2. Стоимость
Стоимость услуг составляет 100 000 рублей.

3. Срок
Договор действует до 31 декабря 2024 года.
```

**document_v2.docx:**
```
Договор оказания услуг

1. Предмет договора
Исполнитель обязуется оказать услуги, а Заказчик - оплатить их.

2. Стоимость
Стоимость услуг составляет 150 000 рублей.

3. Срок действия
Договор действует до 30 июня 2025 года.
```

Система должна обнаружить:
- Изменение стоимости (финансовый параметр, высокое влияние)
- Изменение срока (даты, высокое влияние)
- Изменение заголовка "Срок" → "Срок действия" (техническое, низкое влияние)

Удачи! 🚀



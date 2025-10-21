# Руководство по развёртыванию DocCompare

## Локальная разработка

### 1. Предварительные требования

- Python 3.11+
- Docker Desktop
- Git
- Tesseract OCR (для работы с отсканированными PDF)

### 2. Установка Tesseract

**macOS:**
```bash
brew install tesseract tesseract-lang
```

**Ubuntu/Debian:**
```bash
sudo apt-get install tesseract-ocr tesseract-ocr-rus tesseract-ocr-eng
```

### 3. Клонирование и настройка

```bash
# Клонировать репозиторий
git clone <repo-url>
cd DocCompare

# Создать виртуальное окружение
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Установить зависимости
pip install -r requirements.txt

# Настроить переменные окружения
cp .env.example .env
# Отредактировать .env и добавить API ключи
```

### 4. Запуск инфраструктуры

```bash
# Запустить Docker контейнеры
make docker-up

# Дождаться готовности сервисов (10-15 секунд)
# Проверить статус
docker-compose ps
```

### 5. Применить миграции БД

```bash
# Создать первую миграцию
make migrate-create
# Ввести: "Initial migration"

# Применить миграции
make migrate
```

### 6. Запустить сервер

```bash
# Режим разработки с hot-reload
make run

# Или напрямую
uvicorn app.main:app --reload
```

Приложение будет доступно на http://localhost:8000

### 7. Проверка работоспособности

```bash
# Health check
curl http://localhost:8000/health

# API документация
# Открыть в браузере: http://localhost:8000/docs
```

## Тестирование

```bash
# Запустить все тесты
make test

# Запустить с покрытием
pytest --cov=app --cov-report=html

# Открыть отчёт
open htmlcov/index.html
```

## Проверка кода

```bash
# Линтинг
make lint

# Форматирование
make format
```

## Развёртывание на сервере

### 1. Подготовка сервера

```bash
# Установить Docker и Docker Compose
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh

sudo apt-get install docker-compose-plugin

# Установить Python 3.11+
sudo apt-get install python3.11 python3.11-venv python3-pip

# Установить Tesseract
sudo apt-get install tesseract-ocr tesseract-ocr-rus tesseract-ocr-eng
```

### 2. Клонирование проекта

```bash
cd /opt
sudo git clone <repo-url> doccompare
cd doccompare
sudo chown -R $USER:$USER .
```

### 3. Конфигурация для продакшена

```bash
# Создать .env для продакшена
cp .env.example .env

# Отредактировать критичные параметры:
# - DEBUG=false
# - Сложные пароли для БД
# - Реальные API ключи
# - Настройки безопасности

nano .env
```

### 4. Настройка systemd сервиса

Создать `/etc/systemd/system/doccompare.service`:

```ini
[Unit]
Description=DocCompare API Service
After=network.target docker.service
Requires=docker.service

[Service]
Type=simple
User=www-data
WorkingDirectory=/opt/doccompare
Environment="PATH=/opt/doccompare/venv/bin"
ExecStart=/opt/doccompare/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Активировать:

```bash
sudo systemctl daemon-reload
sudo systemctl enable doccompare
sudo systemctl start doccompare
sudo systemctl status doccompare
```

### 5. Nginx reverse proxy

Установить Nginx:

```bash
sudo apt-get install nginx
```

Создать `/etc/nginx/sites-available/doccompare`:

```nginx
server {
    listen 80;
    server_name doccompare.example.com;

    client_max_body_size 100M;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Увеличенный таймаут для обработки больших файлов
        proxy_read_timeout 300s;
        proxy_connect_timeout 75s;
    }

    location /metrics {
        deny all;
    }
}
```

Активировать:

```bash
sudo ln -s /etc/nginx/sites-available/doccompare /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### 6. SSL сертификат (Let's Encrypt)

```bash
sudo apt-get install certbot python3-certbot-nginx
sudo certbot --nginx -d doccompare.example.com
```

### 7. Мониторинг

Grafana будет доступна на http://server-ip:3000
- Логин: admin
- Пароль: admin (изменить при первом входе)

Prometheus: http://server-ip:9090

### 8. Бэкапы БД

Создать скрипт `/opt/doccompare/backup.sh`:

```bash
#!/bin/bash
BACKUP_DIR="/opt/backups/doccompare"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p $BACKUP_DIR

# Бэкап PostgreSQL
docker exec doccompare-postgres pg_dump -U doccompare doccompare > \
    $BACKUP_DIR/db_backup_$DATE.sql

# Сжать
gzip $BACKUP_DIR/db_backup_$DATE.sql

# Удалить старые бэкапы (старше 30 дней)
find $BACKUP_DIR -name "*.gz" -mtime +30 -delete
```

Добавить в cron:

```bash
sudo crontab -e

# Ежедневный бэкап в 2:00
0 2 * * * /opt/doccompare/backup.sh
```

## Обновление версии

```bash
cd /opt/doccompare
git pull
source venv/bin/activate
pip install -r requirements.txt
make migrate
sudo systemctl restart doccompare
```

## Логи

```bash
# Логи приложения
sudo journalctl -u doccompare -f

# Логи Docker
docker-compose logs -f

# Логи конкретного сервиса
docker-compose logs -f postgres
```

## Troubleshooting

### Проблема: MinIO не запускается

```bash
# Проверить порты
sudo lsof -i :9000
sudo lsof -i :9001

# Пересоздать контейнер
docker-compose down
docker volume rm doccompare_minio_data
docker-compose up -d minio
```

### Проблема: Ошибка подключения к БД

```bash
# Проверить статус
docker-compose ps postgres

# Проверить логи
docker-compose logs postgres

# Пересоздать БД
docker-compose down
docker volume rm doccompare_postgres_data
docker-compose up -d postgres
make migrate
```

### Проблема: OCR не работает

```bash
# Проверить установку Tesseract
tesseract --version

# Проверить языки
tesseract --list-langs

# Установить недостающие языки
sudo apt-get install tesseract-ocr-rus tesseract-ocr-eng
```

## Масштабирование

Для высоких нагрузок:

1. **Горизонтальное масштабирование API**:
   - Запустить несколько экземпляров приложения
   - Использовать Nginx для балансировки нагрузки

2. **Очередь задач**:
   - Добавить Celery для асинхронной обработки
   - Использовать Redis как брокер сообщений

3. **База данных**:
   - Настроить репликацию PostgreSQL
   - Использовать connection pooling (PgBouncer)

4. **Кэширование**:
   - Расширить использование Redis
   - Кэшировать результаты анализа

5. **Хранилище**:
   - Перейти на S3 вместо MinIO
   - Настроить CDN для статики



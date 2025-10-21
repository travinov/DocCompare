# 📖 Руководство по использованию DocCompare

## ✅ Система запущена и работает!

- API: http://localhost:8000
- Swagger UI: http://localhost:8000/docs
- GPT-4: настроен и работает

---

## 🚀 Быстрый старт

### Вариант 1: Через Python скрипт (рекомендуется)

```bash
cd '/Users/travinov-sv/Library/Mobile Documents/com~apple~CloudDocs/Python Project/DocCompare'
source venv/bin/activate

# Сравнить документы (перетащите файлы мышкой в терминал)
python compare_my_docs.py <файл1> <файл2>
```

**Что происходит:**
1. Документы загружаются на сервер
2. Извлекается текст
3. Выполняется diff-анализ
4. GPT-4 анализирует семантику
5. Генерируются отчёты

**Результат:**
- Показывается Case ID
- Выводится сводка GPT-4
- Сохраняется HTML отчёт
- Время: 10-30 секунд

---

### Вариант 2: Через Swagger UI

1. Откройте http://localhost:8000/docs
2. Найдите `POST /api/v1/compare/`
3. Нажмите "Try it out"
4. Загрузите два файла
5. Нажмите "Execute"
6. Скопируйте `id` из ответа
7. Используйте `GET /api/v1/compare/{id}` для просмотра результатов

---

## 📊 Получение детального списка изменений

После того как документы обработаны, вы можете получить **детальный нумерованный список изменений** в стиле diff:

```bash
source venv/bin/activate

# Получить список изменений на экран
python show_diff_list.py <case_id>

# Сохранить в файл
python show_diff_list.py <case_id> --save изменения.md
```

**Что включает детальный diff:**
- ✅ Нумерация всех изменений
- ✅ Статус каждого: ➕ добавлено / ➖ удалено / ✏️ изменено
- ✅ Конкретные фрагменты: что было → что стало
- ✅ Разбивка на предложения
- ✅ GPT-4 анализ
- ✅ Категории и влияние

**Пример для вашего POSH Policy:**
```bash
python show_diff_list.py 3b447bcc-1aa9-456e-89f8-7ce800ccfb27 --save POSH_changes.md
```

---

## 📝 Пример полного рабочего процесса

```bash
# 1. Перейдите в директорию проекта
cd '/Users/travinov-sv/Library/Mobile Documents/com~apple~CloudDocs/Python Project/DocCompare'

# 2. Активируйте виртуальное окружение
source venv/bin/activate

# 3. Сравните документы
python compare_my_docs.py ~/Desktop/contract_v1.docx ~/Desktop/contract_v2.docx

# 4. Из вывода скопируйте Case ID (например: abc123...)

# 5. Получите детальный diff список
python show_diff_list.py abc123... --save contract_changes.md

# 6. Откройте отчёт
open contract_changes.md
```

---

## 🎯 Что вы получаете

### 1. Общая сводка GPT-4
Краткое резюме что изменилось в целом

### 2. HTML отчёт
Красивая веб-страница с:
- Статистикой
- Визуализацией изменений
- Группировкой по категориям

### 3. Детальный diff-список (Markdown)
Нумерованный список всех изменений:
```
1. ✏️ MODIFIED - 🔴 СЕМАНТИЧЕСКОЕ
   Категория: FINANCIAL
   Влияние: 🔴 HIGH
   
   GPT-4 Анализ:
   > Стоимость увеличена с 100,000 до 150,000

   ❌ Было: Стоимость услуг 100 000 рублей
   ✅ Стало: Стоимость услуг 150 000 рублей
```

### 4. JSON данные
Для программной обработки

---

## 💡 Полезные команды

```bash
# Проверить статус системы
curl http://localhost:8000/health

# Получить информацию о кейсе
curl http://localhost:8000/api/v1/compare/<case_id>

# Скачать HTML отчёт
curl http://localhost:8000/api/v1/compare/<case_id>/report/html > report.html

# Просмотреть все кейсы в БД
# (пока нет endpoint, но данные в PostgreSQL)
```

---

## 🔧 Управление системой

### Запуск (если остановлена)

```bash
# 1. Запустить Docker контейнеры
docker-compose up -d

# 2. Активировать окружение
source venv/bin/activate

# 3. Запустить API сервер
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### Остановка

```bash
# Остановить API сервер
# Нажмите Ctrl+C в терминале где запущен сервер

# Остановить Docker
docker-compose down
```

---

## 📚 Документация

- **README.md** - обзор проекта
- **QUICKSTART.md** - быстрый старт
- **API_EXAMPLES.md** - примеры API
- **DEPLOYMENT.md** - развёртывание на сервере

---

## 🆘 Помощь

**Если что-то не работает:**

1. Проверьте что Docker Desktop запущен
2. Убедитесь что порт 8000 свободен: `lsof -i:8000`
3. Проверьте логи: `docker-compose logs`
4. Перезапустите систему: `docker-compose restart`

**GitHub:** https://github.com/travinov/DocCompare

---

**Последнее обновление:** 21 октября 2025



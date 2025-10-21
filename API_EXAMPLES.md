# Примеры использования API

## Базовые операции

### 1. Health Check

```bash
curl http://localhost:8000/health
```

Ответ:
```json
{
  "status": "healthy"
}
```

### 2. Получение информации о сервисе

```bash
curl http://localhost:8000/
```

Ответ:
```json
{
  "name": "DocCompare",
  "version": "1.0.0",
  "status": "running"
}
```

## Сравнение документов

### 3. Загрузка документов для сравнения

```bash
curl -X POST http://localhost:8000/api/v1/compare \
  -F "base_file=@/path/to/document_v1.docx" \
  -F "target_file=@/path/to/document_v2.docx"
```

Ответ:
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "pending",
  "created_at": "2025-10-21T10:30:00",
  "updated_at": "2025-10-21T10:30:00",
  "total_changes": 0,
  "semantic_changes_count": 0,
  "technical_changes_count": 0,
  "documents": [
    {
      "id": "660e8400-e29b-41d4-a716-446655440001",
      "document_type": "base",
      "original_filename": "document_v1.docx",
      "file_format": "docx",
      "file_size": 15420,
      "is_scanned": false,
      "created_at": "2025-10-21T10:30:00"
    },
    {
      "id": "770e8400-e29b-41d4-a716-446655440002",
      "document_type": "target",
      "original_filename": "document_v2.docx",
      "file_format": "docx",
      "file_size": 15890,
      "is_scanned": false,
      "created_at": "2025-10-21T10:30:00"
    }
  ],
  "changes": []
}
```

### 4. Получение статуса обработки

```bash
curl http://localhost:8000/api/v1/compare/550e8400-e29b-41d4-a716-446655440000
```

Ответ (во время обработки):
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "analyzing",
  "created_at": "2025-10-21T10:30:00",
  "updated_at": "2025-10-21T10:30:45",
  "total_changes": 0,
  "semantic_changes_count": 0,
  "technical_changes_count": 0
}
```

Ответ (после завершения):
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "completed",
  "created_at": "2025-10-21T10:30:00",
  "updated_at": "2025-10-21T10:31:20",
  "total_changes": 15,
  "semantic_changes_count": 8,
  "technical_changes_count": 7,
  "overall_impact": "high",
  "summary": "Обнаружено 8 семантически значимых изменений...",
  "processing_time": 80.5,
  "documents": [...],
  "changes": [...]
}
```

### 5. Получение списка изменений

```bash
# Все изменения
curl http://localhost:8000/api/v1/compare/550e8400-e29b-41d4-a716-446655440000/changes

# Только семантические изменения
curl "http://localhost:8000/api/v1/compare/550e8400-e29b-41d4-a716-446655440000/changes?semantic_only=true"
```

Ответ:
```json
[
  {
    "id": "880e8400-e29b-41d4-a716-446655440003",
    "position": 1,
    "section": "Раздел 3. Стоимость услуг",
    "change_type": "modified",
    "old_text": "Стоимость услуг составляет 100 000 рублей",
    "new_text": "Стоимость услуг составляет 150 000 рублей",
    "is_semantic_change": true,
    "category": "financial",
    "impact": "high",
    "llm_summary": "Увеличена стоимость услуг с 100 000 до 150 000 рублей",
    "similarity_score": 0.89
  },
  {
    "id": "990e8400-e29b-41d4-a716-446655440004",
    "position": 2,
    "change_type": "modified",
    "old_text": "Срок действия договора до 31 декабря 2024 года",
    "new_text": "Срок действия договора до 30 июня 2025 года",
    "is_semantic_change": true,
    "category": "dates",
    "impact": "high",
    "llm_summary": "Изменён срок действия договора с 31.12.2024 на 30.06.2025"
  }
]
```

## Получение отчётов

### 6. Получение ссылок на отчёты

```bash
curl http://localhost:8000/api/v1/compare/550e8400-e29b-41d4-a716-446655440000/reports
```

Ответ:
```json
{
  "case_id": "550e8400-e29b-41d4-a716-446655440000",
  "html_url": "http://localhost:9000/doccompare/reports/550e8400.../report.html?X-Amz-...",
  "pdf_url": "http://localhost:9000/doccompare/reports/550e8400.../report.pdf?X-Amz-...",
  "json_url": "http://localhost:9000/doccompare/reports/550e8400.../report.json?X-Amz-..."
}
```

### 7. Получение HTML отчёта напрямую

```bash
curl http://localhost:8000/api/v1/compare/550e8400-e29b-41d4-a716-446655440000/report/html > report.html
```

Или открыть в браузере:
```
http://localhost:8000/api/v1/compare/550e8400-e29b-41d4-a716-446655440000/report/html
```

### 8. Скачивание PDF отчёта

```bash
# Получить ссылку
REPORT_URL=$(curl -s http://localhost:8000/api/v1/compare/550e8400-e29b-41d4-a716-446655440000/reports | jq -r .pdf_url)

# Скачать
curl "$REPORT_URL" -o report.pdf
```

## Удаление кейса

### 9. Удаление кейса и всех файлов

```bash
curl -X DELETE http://localhost:8000/api/v1/compare/550e8400-e29b-41d4-a716-446655440000
```

Ответ:
```json
{
  "status": "deleted",
  "case_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

## Python примеры

### Сравнение документов (Python)

```python
import requests
import time

API_URL = "http://localhost:8000/api/v1"

# Загружаем документы
with open("document_v1.docx", "rb") as base_file, \
     open("document_v2.docx", "rb") as target_file:
    
    files = {
        "base_file": ("document_v1.docx", base_file),
        "target_file": ("document_v2.docx", target_file),
    }
    
    response = requests.post(f"{API_URL}/compare", files=files)
    case = response.json()
    case_id = case["id"]
    
    print(f"Created case: {case_id}")

# Ждём завершения обработки
while True:
    response = requests.get(f"{API_URL}/compare/{case_id}")
    case = response.json()
    status = case["status"]
    
    print(f"Status: {status}")
    
    if status == "completed":
        print(f"Processing time: {case['processing_time']}s")
        print(f"Total changes: {case['total_changes']}")
        print(f"Semantic changes: {case['semantic_changes_count']}")
        print(f"Summary: {case['summary']}")
        break
    elif status == "failed":
        print(f"Error: {case.get('error_message')}")
        break
    
    time.sleep(2)

# Получаем детальные изменения
response = requests.get(f"{API_URL}/compare/{case_id}/changes?semantic_only=true")
changes = response.json()

for change in changes:
    print(f"\n[{change['category'].upper()}] Impact: {change['impact']}")
    print(f"Summary: {change['llm_summary']}")
    if change.get('old_text'):
        print(f"Old: {change['old_text'][:100]}...")
    if change.get('new_text'):
        print(f"New: {change['new_text'][:100]}...")

# Скачиваем HTML отчёт
response = requests.get(f"{API_URL}/compare/{case_id}/report/html")
with open("report.html", "wb") as f:
    f.write(response.content)

print("\nReport saved to report.html")
```

### Async Python пример

```python
import asyncio
import httpx

async def compare_documents():
    async with httpx.AsyncClient() as client:
        # Загрузка документов
        files = {
            "base_file": open("document_v1.docx", "rb"),
            "target_file": open("document_v2.docx", "rb"),
        }
        
        response = await client.post(
            "http://localhost:8000/api/v1/compare",
            files=files
        )
        case_id = response.json()["id"]
        
        # Polling статуса
        while True:
            response = await client.get(
                f"http://localhost:8000/api/v1/compare/{case_id}"
            )
            data = response.json()
            
            if data["status"] == "completed":
                return data
            elif data["status"] == "failed":
                raise Exception(data.get("error_message"))
            
            await asyncio.sleep(2)

# Запуск
result = asyncio.run(compare_documents())
print(f"Found {result['semantic_changes_count']} semantic changes")
```

## JavaScript/TypeScript пример

```typescript
async function compareDocuments(baseFile: File, targetFile: File) {
  const formData = new FormData();
  formData.append('base_file', baseFile);
  formData.append('target_file', targetFile);
  
  // Создание кейса
  const createResponse = await fetch('http://localhost:8000/api/v1/compare', {
    method: 'POST',
    body: formData,
  });
  
  const case_data = await createResponse.json();
  const caseId = case_data.id;
  
  // Polling статуса
  while (true) {
    const statusResponse = await fetch(
      `http://localhost:8000/api/v1/compare/${caseId}`
    );
    const data = await statusResponse.json();
    
    if (data.status === 'completed') {
      return data;
    } else if (data.status === 'failed') {
      throw new Error(data.error_message);
    }
    
    await new Promise(resolve => setTimeout(resolve, 2000));
  }
}

// Использование
const baseFileInput = document.getElementById('base-file') as HTMLInputElement;
const targetFileInput = document.getElementById('target-file') as HTMLInputElement;

const baseFile = baseFileInput.files[0];
const targetFile = targetFileInput.files[0];

const result = await compareDocuments(baseFile, targetFile);
console.log(`Semantic changes: ${result.semantic_changes_count}`);
console.log(`Summary: ${result.summary}`);
```

## Swagger/OpenAPI

Интерактивная документация API доступна по адресу:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json



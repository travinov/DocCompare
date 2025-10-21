#!/usr/bin/env python3
"""
Скрипт для сравнения ваших документов через DocCompare API.

Использование:
    python compare_my_docs.py путь/к/старому/документу.docx путь/к/новому/документу.docx
"""

import sys
import time
import requests
from pathlib import Path


API_URL = "http://localhost:8000/api/v1"


def compare_documents(base_file_path: str, target_file_path: str):
    """Сравнивает два документа и показывает результаты."""
    
    base_path = Path(base_file_path)
    target_path = Path(target_file_path)
    
    # Проверка существования файлов
    if not base_path.exists():
        print(f"❌ Файл не найден: {base_file_path}")
        return
    
    if not target_path.exists():
        print(f"❌ Файл не найден: {target_file_path}")
        return
    
    print("📤 Загрузка документов на сервер...")
    print(f"   Базовый: {base_path.name}")
    print(f"   Новый: {target_path.name}")
    print()
    
    # Загрузка файлов
    with open(base_path, "rb") as base_file, open(target_path, "rb") as target_file:
        files = {
            "base_file": (base_path.name, base_file),
            "target_file": (target_path.name, target_file),
        }
        
        try:
            response = requests.post(f"{API_URL}/compare/", files=files)
            response.raise_for_status()
        except Exception as e:
            print(f"❌ Ошибка при загрузке: {e}")
            return
    
    case_data = response.json()
    case_id = case_data["id"]
    
    print(f"✅ Документы загружены!")
    print(f"📋 Case ID: {case_id}")
    print()
    print("⏳ Обработка документов...")
    print("   (Это займёт 10-30 секунд)")
    print()
    
    # Ожидание завершения обработки
    dots = 0
    while True:
        time.sleep(2)
        
        try:
            response = requests.get(f"{API_URL}/compare/{case_id}")
            response.raise_for_status()
            data = response.json()
        except Exception as e:
            print(f"\n❌ Ошибка при проверке статуса: {e}")
            return
        
        status = data["status"]
        
        # Показываем прогресс
        dots = (dots + 1) % 4
        print(f"\r   Статус: {status.ljust(15)} {'.' * dots}   ", end="", flush=True)
        
        if status == "completed":
            print("\n")
            print("=" * 60)
            print("🎉 ОБРАБОТКА ЗАВЕРШЕНА!")
            print("=" * 60)
            print()
            print(f"⏱️  Время обработки: {data['processing_time']:.2f} секунд")
            print()
            print("📊 РЕЗУЛЬТАТЫ:")
            print(f"   Всего изменений: {data['total_changes']}")
            print(f"   Семантических: {data['semantic_changes_count']} 🔴")
            print(f"   Технических: {data['technical_changes_count']} 🟡")
            print(f"   Общее влияние: {(data['overall_impact'] or 'N/A').upper()}")
            print()
            print("📝 СВОДКА:")
            print(f"   {data['summary']}")
            print()
            
            # Получаем детали изменений
            try:
                changes_response = requests.get(
                    f"{API_URL}/compare/{case_id}/changes",
                    params={"semantic_only": True}
                )
                changes_response.raise_for_status()
                semantic_changes = changes_response.json()
                if isinstance(semantic_changes, str):
                    semantic_changes = []
            except Exception as e:
                print(f"⚠️ Не удалось загрузить детали изменений: {e}")
                semantic_changes = []
            
            if semantic_changes and isinstance(semantic_changes, list):
                print("🔍 СЕМАНТИЧЕСКИЕ ИЗМЕНЕНИЯ:")
                print()
                for idx, change in enumerate(semantic_changes, 1):
                    if not isinstance(change, dict):
                        continue
                    category = change.get('category', 'прочее')
                    impact = change.get('impact', 'средний')
                    summary = change.get('llm_summary', '')
                    
                    print(f"   {idx}. [{category.upper()}] Влияние: {impact.upper()}")
                    if summary:
                        print(f"      💡 {summary}")
                    
                    old_text = change.get('old_text', '')
                    new_text = change.get('new_text', '')
                    
                    if old_text and len(old_text) < 200:
                        print(f"      ❌ Было: {old_text}")
                    if new_text and len(new_text) < 200:
                        print(f"      ✅ Стало: {new_text}")
                    print()
            
            # Сохраняем HTML отчёт
            report_response = requests.get(f"{API_URL}/compare/{case_id}/report/html")
            report_path = Path(f"report_{case_id}.html")
            report_path.write_bytes(report_response.content)
            
            print("=" * 60)
            print(f"📄 HTML отчёт сохранён: {report_path.name}")
            print("   Открыть отчёт:")
            print(f"   open {report_path.name}")
            print()
            print(f"🌐 Или откройте в браузере:")
            print(f"   http://localhost:8000/api/v1/compare/{case_id}/report/html")
            print("=" * 60)
            
            break
            
        elif status == "failed":
            print("\n")
            print(f"❌ Ошибка обработки: {data.get('error_message')}")
            break


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Использование:")
        print(f"  python {sys.argv[0]} <старый_документ> <новый_документ>")
        print()
        print("Пример:")
        print(f"  python {sys.argv[0]} договор_v1.docx договор_v2.docx")
        sys.exit(1)
    
    base_file = sys.argv[1]
    target_file = sys.argv[2]
    
    compare_documents(base_file, target_file)


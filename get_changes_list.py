#!/usr/bin/env python3
"""
Скрипт для получения изменений в формате маркированного списка.

Использование:
    python get_changes_list.py <case_id>
    python get_changes_list.py <case_id> --save changes.md
"""

import sys
import requests
from pathlib import Path


API_URL = "http://localhost:8000/api/v1"


def get_changes_as_list(case_id: str, save_to: str = None, semantic_only: bool = False):
    """Получает изменения в формате маркированного списка."""
    
    try:
        # Получаем информацию о кейсе
        response = requests.get(f"{API_URL}/compare/{case_id}")
        response.raise_for_status()
        case_data = response.json()
    except Exception as e:
        print(f"❌ Ошибка при получении данных кейса: {e}")
        return
    
    # Формируем маркированный список
    lines = []
    lines.append("# Отчёт о сравнении документов\n")
    lines.append(f"**Case ID:** `{case_id}`\n")
    lines.append(f"**Статус:** {case_data['status']}\n")
    lines.append(f"**Дата:** {case_data['created_at']}\n")
    if case_data.get('processing_time'):
        lines.append(f"**Время обработки:** {case_data['processing_time']:.2f} сек.\n")
    lines.append("\n---\n\n")
    
    # Статистика
    lines.append("## 📊 Статистика\n\n")
    lines.append(f"- **Всего изменений:** {case_data['total_changes']}\n")
    lines.append(f"- **Семантических:** {case_data['semantic_changes_count']} 🔴\n")
    lines.append(f"- **Технических:** {case_data['technical_changes_count']} 🟡\n")
    lines.append(f"- **Общее влияние:** {(case_data.get('overall_impact') or 'N/A').upper()}\n")
    lines.append("\n")
    
    # Сводка
    if case_data.get('summary'):
        lines.append("## 📝 Общая сводка\n\n")
        lines.append(f"{case_data['summary']}\n\n")
    
    lines.append("---\n\n")
    
    # Получаем изменения
    try:
        params = {"semantic_only": "true"} if semantic_only else {}
        response = requests.get(f"{API_URL}/compare/{case_id}/changes", params=params)
        response.raise_for_status()
        changes = response.json()
        
        if not isinstance(changes, list):
            changes = case_data.get('changes', [])
    except:
        changes = case_data.get('changes', [])
    
    # Группируем по категориям
    by_category = {}
    for change in changes:
        if semantic_only and not change.get('is_semantic_change'):
            continue
        
        category = change.get('category', 'other')
        if category not in by_category:
            by_category[category] = []
        by_category[category].append(change)
    
    # Категории с описаниями
    category_names = {
        'dates': '📅 Сроки и даты',
        'financial': '💰 Финансовые параметры',
        'obligations': '📋 Обязательства',
        'conditions': '📜 Условия',
        'parties': '👥 Стороны договора',
        'technical': '⚙️ Технические детали',
        'other': '📌 Прочее',
    }
    
    if semantic_only:
        lines.append("## 🔍 Семантические изменения\n\n")
    else:
        lines.append("## 📋 Все изменения\n\n")
    
    if not by_category:
        lines.append("_Изменений не обнаружено_\n")
    else:
        for category, category_changes in by_category.items():
            category_name = category_names.get(category, f'📌 {category}')
            lines.append(f"### {category_name}\n\n")
            
            for idx, change in enumerate(category_changes, 1):
                change_type = change.get('change_type', 'unknown')
                impact = change.get('impact', 'medium')
                summary = change.get('llm_summary', '')
                
                # Иконка типа изменения
                type_icon = {
                    'added': '➕',
                    'removed': '➖',
                    'modified': '✏️',
                }.get(change_type, '•')
                
                # Иконка влияния
                impact_icon = {
                    'high': '🔴',
                    'medium': '🟡',
                    'low': '🟢',
                }.get(impact, '⚪')
                
                lines.append(f"{idx}. {type_icon} **{change_type.upper()}** {impact_icon} _{impact}_\n\n")
                
                if summary:
                    lines.append(f"   **Анализ:** {summary}\n\n")
                
                old_text = change.get('old_text', '')
                new_text = change.get('new_text', '')
                
                if old_text and len(old_text) < 300:
                    lines.append(f"   **Было:**\n")
                    lines.append(f"   > {old_text}\n\n")
                elif old_text:
                    lines.append(f"   **Было:** _{len(old_text)} символов_\n\n")
                
                if new_text and len(new_text) < 300:
                    lines.append(f"   **Стало:**\n")
                    lines.append(f"   > {new_text}\n\n")
                elif new_text:
                    lines.append(f"   **Стало:** _{len(new_text)} символов_\n\n")
                
                if change.get('similarity_score'):
                    lines.append(f"   _Схожесть: {change['similarity_score']*100:.1f}%_\n\n")
                
                lines.append("   ---\n\n")
            
            lines.append("\n")
    
    # Объединяем в текст
    markdown_text = "".join(lines)
    
    # Вывод
    print(markdown_text)
    
    # Сохранение в файл
    if save_to:
        Path(save_to).write_text(markdown_text, encoding='utf-8')
        print(f"\n✅ Отчёт сохранён: {save_to}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Использование:")
        print(f"  python {sys.argv[0]} <case_id>")
        print(f"  python {sys.argv[0]} <case_id> --save changes.md")
        print(f"  python {sys.argv[0]} <case_id> --semantic  # только семантические")
        print()
        print("Пример:")
        print(f"  python {sys.argv[0]} 3b447bcc-1aa9-456e-89f8-7ce800ccfb27")
        print(f"  python {sys.argv[0]} 3b447bcc-1aa9-456e-89f8-7ce800ccfb27 --save report.md")
        sys.exit(1)
    
    case_id = sys.argv[1]
    save_to = None
    semantic_only = False
    
    if "--save" in sys.argv:
        idx = sys.argv.index("--save")
        if idx + 1 < len(sys.argv):
            save_to = sys.argv[idx + 1]
    
    if "--semantic" in sys.argv:
        semantic_only = True
    
    get_changes_as_list(case_id, save_to, semantic_only)



#!/usr/bin/env python3
"""
Показывает детальный нумерованный список изменений в стиле diff.

Использование:
    python show_diff_list.py <case_id>
    python show_diff_list.py <case_id> --save changes.md
"""

import sys
import difflib
import requests
from pathlib import Path


API_URL = "http://localhost:8000/api/v1"


def split_into_sentences(text: str):
    """Разбивает текст на предложения."""
    import re
    # Простое разбиение по точкам, вопросам и восклицаниям
    sentences = re.split(r'(?<=[.!?])\s+', text)
    return [s.strip() for s in sentences if s.strip()]


def show_detailed_diff(case_id: str, save_to: str = None):
    """Показывает детальный diff."""
    
    try:
        response = requests.get(f"{API_URL}/compare/{case_id}")
        response.raise_for_status()
        case_data = response.json()
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return
    
    # Получаем документы с полным текстом
    docs = case_data.get('documents', [])
    base_doc = next((d for d in docs if d['document_type'] == 'base'), None)
    target_doc = next((d for d in docs if d['document_type'] == 'target'), None)
    
    lines = []
    
    # Заголовок
    lines.append("# 📋 Детальный Diff-отчёт\n\n")
    lines.append(f"**Case ID:** `{case_id}`\n\n")
    
    # Документы
    lines.append("## 📄 Сравниваемые документы\n\n")
    if base_doc:
        lines.append(f"**📕 Базовый:**  {base_doc['original_filename']}\n")
    if target_doc:
        lines.append(f"**📗 Новый:**    {target_doc['original_filename']}\n")
    lines.append("\n")
    
    # Статистика
    lines.append("## 📊 Статистика\n\n")
    lines.append(f"- Статус: `{case_data['status']}`\n")
    lines.append(f"- Время обработки: {case_data.get('processing_time', 0):.2f} сек.\n")
    lines.append(f"- Всего изменений: **{case_data['total_changes']}**\n")
    lines.append(f"- 🔴 Семантических: **{case_data['semantic_changes_count']}**\n")
    lines.append(f"- 🟡 Технических: **{case_data['technical_changes_count']}**\n")
    lines.append(f"- Влияние: **{(case_data.get('overall_impact') or 'N/A').upper()}**\n")
    lines.append("\n")
    
    # Сводка GPT-4
    if case_data.get('summary'):
        lines.append("## 💡 Общая сводка GPT-4\n\n")
        lines.append(f"> {case_data['summary']}\n\n")
    
    lines.append("---\n\n")
    
    # Изменения
    changes = case_data.get('changes', [])
    
    if not changes:
        lines.append("_Изменений не найдено_\n")
    else:
        lines.append("## 🔍 Нумерованный список всех изменений\n\n")
        
        for idx, change in enumerate(changes, 1):
            change_type = change.get('change_type', 'unknown')
            is_semantic = change.get('is_semantic_change', False)
            category = change.get('category', 'other')
            impact = change.get('impact', 'medium')
            
            # Иконки
            type_icon = {
                'added': '➕',
                'removed': '➖',
                'modified': '✏️',
            }.get(change_type, '•')
            
            impact_icon = {
                'high': '🔴',
                'medium': '🟡',
                'low': '🟢',
            }.get(impact, '⚪')
            
            semantic_badge = "🔴 СЕМАНТИЧЕСКОЕ" if is_semantic else "🟡 ТЕХНИЧЕСКОЕ"
            
            # Заголовок изменения
            lines.append(f"### Изменение #{idx} {type_icon} {change_type.upper()} - {semantic_badge}\n\n")
            
            # Метаданные
            lines.append(f"**Категория:** {category.upper()}  \n")
            lines.append(f"**Влияние:** {impact_icon} {impact.upper()}  \n")
            if change.get('position') is not None:
                lines.append(f"**Позиция:** {change['position']}  \n")
            lines.append("\n")
            
            # Анализ GPT-4
            if change.get('llm_summary'):
                lines.append(f"**💡 Анализ GPT-4:**\n\n")
                lines.append(f"> {change['llm_summary']}\n\n")
            
            # Детальное сравнение текстов
            old_text = change.get('old_text', '')
            new_text = change.get('new_text', '')
            
            if change_type == 'modified' and old_text and new_text:
                # Разбиваем на предложения для детального сравнения
                old_sentences = split_into_sentences(old_text)
                new_sentences = split_into_sentences(new_text)
                
                # Если предложений немного - показываем все
                if len(old_sentences) <=5 and len(new_sentences) <= 5:
                    lines.append("**❌ Было:**\n\n")
                    for sent in old_sentences:
                        lines.append(f"- {sent}\n")
                    lines.append("\n")
                    
                    lines.append("**✅ Стало:**\n\n")
                    for sent in new_sentences:
                        lines.append(f"- {sent}\n")
                    lines.append("\n")
                else:
                    # Если предложений много - показываем diff между ними
                    matcher = difflib.SequenceMatcher(None, old_sentences, new_sentences)
                    
                    diff_lines = []
                    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
                        if tag == 'equal':
                            continue
                        elif tag == 'delete':
                            for i in range(i1, min(i2, i1+3)):  # Первые 3
                                diff_lines.append(f"   ➖ {old_sentences[i][:200]}")
                        elif tag == 'insert':
                            for j in range(j1, min(j2, j1+3)):  # Первые 3
                                diff_lines.append(f"   ➕ {new_sentences[j][:200]}")
                        elif tag == 'replace':
                            for i in range(i1, min(i2, i1+2)):
                                diff_lines.append(f"   ❌ Было: {old_sentences[i][:150]}")
                            for j in range(j1, min(j2, j1+2)):
                                diff_lines.append(f"   ✅ Стало: {new_sentences[j][:150]}")
                    
                    if diff_lines:
                        lines.append("**🔬 Детальные изменения:**\n\n")
                        lines.extend([f"{line}\n" for line in diff_lines[:15]])
                        if len(diff_lines) > 15:
                            lines.append(f"\n   _... и ещё {len(diff_lines) - 15} изменений_\n")
                        lines.append("\n")
                    
                    # Показываем размеры
                    lines.append(f"**Размер текста:**\n")
                    lines.append(f"- Старый: {len(old_text):,} символов ({len(old_sentences)} предложений)\n")
                    lines.append(f"- Новый: {len(new_text):,} символов ({len(new_sentences)} предложений)\n")
                    lines.append(f"- Разница: {len(new_text) - len(old_text):+,} символов\n\n")
            
            elif change_type == 'added' and new_text:
                sentences = split_into_sentences(new_text)
                lines.append(f"**➕ Добавлено ({len(sentences)} предложений):**\n\n")
                for sent in sentences[:5]:
                    lines.append(f"- {sent}\n")
                if len(sentences) > 5:
                    lines.append(f"\n_... и ещё {len(sentences) - 5} предложений_\n")
                lines.append("\n")
            
            elif change_type == 'removed' and old_text:
                sentences = split_into_sentences(old_text)
                lines.append(f"**➖ Удалено ({len(sentences)} предложений):**\n\n")
                for sent in sentences[:5]:
                    lines.append(f"- {sent}\n")
                if len(sentences) > 5:
                    lines.append(f"\n_... и ещё {len(sentences) - 5} предложений_\n")
                lines.append("\n")
            
            lines.append("---\n\n")
    
    markdown = "".join(lines)
    
    # Вывод
    print(markdown)
    
    # Сохранение
    if save_to:
        Path(save_to).write_text(markdown, encoding='utf-8')
        print(f"\n✅ Отчёт сохранён: {save_to}\n")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Использование:")
        print(f"  python {sys.argv[0]} <case_id>")
        print(f"  python {sys.argv[0]} <case_id> --save changes.md")
        print()
        print("Пример:")
        print(f"  python {sys.argv[0]} 3b447bcc-1aa9-456e-89f8-7ce800ccfb27 --save posh_diff.md")
        sys.exit(1)
    
    case_id = sys.argv[1]
    save_to = None
    
    if "--save" in sys.argv:
        idx = sys.argv.index("--save")
        if idx + 1 < len(sys.argv):
            save_to = sys.argv[idx + 1]
    
    show_detailed_diff(case_id, save_to)
PYEOF


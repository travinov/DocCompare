#!/usr/bin/env python3
"""
Скрипт для получения детального diff в формате нумерованного списка.

Использование:
    python get_detailed_diff.py <case_id>
    python get_detailed_diff.py <case_id> --save diff.md
"""

import sys
import requests
from pathlib import Path


API_URL = "http://localhost:8000/api/v1"


def get_detailed_diff(case_id: str, save_to: str = None):
    """Получает детальный diff изменений."""
    
    try:
        # Получаем данные кейса
        response = requests.get(f"{API_URL}/compare/{case_id}")
        response.raise_for_status()
        case_data = response.json()
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return
    
    # Получаем документы
    docs = case_data.get('documents', [])
    if len(docs) < 2:
        print("❌ Недостаточно документов")
        return
    
    base_doc = next((d for d in docs if d['document_type'] == 'base'), None)
    target_doc = next((d for d in docs if d['document_type'] == 'target'), None)
    
    # Формируем отчёт
    lines = []
    
    lines.append("# 📋 Детальный Diff-отчёт\n\n")
    lines.append(f"**Case ID:** `{case_id}`\n\n")
    lines.append("## 📄 Документы\n\n")
    if base_doc:
        lines.append(f"**📕 Базовый:** {base_doc['original_filename']}\n")
    if target_doc:
        lines.append(f"**📗 Новый:** {target_doc['original_filename']}\n")
    lines.append("\n")
    
    lines.append("## 📊 Статистика\n\n")
    lines.append(f"- **Статус:** {case_data['status']}\n")
    lines.append(f"- **Всего изменений:** {case_data['total_changes']}\n")
    lines.append(f"- **Семантических:** {case_data['semantic_changes_count']} 🔴\n")
    lines.append(f"- **Технических:** {case_data['technical_changes_count']} 🟡\n")
    lines.append(f"- **Влияние:** {(case_data.get('overall_impact') or 'N/A').upper()}\n")
    
    if case_data.get('summary'):
        lines.append(f"\n**Сводка GPT-4:** {case_data['summary']}\n")
    
    lines.append("\n---\n\n")
    
    # Получаем изменения
    changes = case_data.get('changes', [])
    
    if not changes:
        lines.append("_Изменений не найдено_\n")
    else:
        lines.append("## 🔍 Детальный список изменений\n\n")
        
        # Разбиваем тексты на предложения для детального анализа
        from app.services.diff.detailed_diff import DetailedDiffAnalyzer
        
        # Если есть нормализованные тексты, используем их
        try:
            # Получаем полные тексты из БД
            base_text = ""
            target_text = ""
            
            # Используем данные из changes
            for change in changes:
                if change.get('old_text'):
                    base_text += change['old_text'] + " "
                if change.get('new_text'):
                    target_text += change['new_text'] + " "
            
            if base_text and target_text:
                analyzer = DetailedDiffAnalyzer()
                detailed_changes = analyzer.get_detailed_changes(base_text, target_text)
            else:
                detailed_changes = []
        except:
            detailed_changes = []
        
        # Выводим изменения
        if detailed_changes:
            for change in detailed_changes:
                num = change['number']
                status = change['status']
                change_type = change['type']
                
                lines.append(f"### {num}. {status}\n\n")
                
                if change_type == 'modified':
                    lines.append(f"**Тип:** Модификация\n\n")
                    lines.append(f"**❌ Было:**\n")
                    lines.append(f"```\n{change['old_text']}\n```\n\n")
                    lines.append(f"**✅ Стало:**\n")
                    lines.append(f"```\n{change['new_text']}\n```\n\n")
                    
                    # Детали на уровне слов
                    if change.get('word_changes'):
                        lines.append(f"**📝 Детали изменений:**\n\n")
                        for wc in change['word_changes']:
                            if wc['type'] == 'added':
                                lines.append(f"- ➕ Добавлено: `{wc['words']}`\n")
                            elif wc['type'] == 'removed':
                                lines.append(f"- ➖ Удалено: `{wc['words']}`\n")
                            elif wc['type'] == 'changed':
                                lines.append(f"- ✏️ Изменено: `{wc['old_words']}` → `{wc['new_words']}`\n")
                        lines.append("\n")
                    
                    if change.get('similarity'):
                        lines.append(f"_Схожесть: {change['similarity']*100:.1f}%_\n\n")
                
                elif change_type == 'added':
                    lines.append(f"**Тип:** Добавление\n\n")
                    lines.append(f"```\n{change['text']}\n```\n\n")
                
                elif change_type == 'removed':
                    lines.append(f"**Тип:** Удаление\n\n")
                    lines.append(f"```\n{change['text']}\n```\n\n")
                
                lines.append("---\n\n")
        else:
            # Используем стандартный формат
            for idx, change in enumerate(changes, 1):
                change_type = change.get('change_type', 'unknown')
                is_semantic = change.get('is_semantic_change', False)
                
                status_icon = {
                    'added': '➕',
                    'removed': '➖',
                    'modified': '✏️',
                }.get(change_type, '•')
                
                semantic_badge = "🔴 СЕМАНТИЧЕСКОЕ" if is_semantic else "🟡 ТЕХНИЧЕСКОЕ"
                
                lines.append(f"### {idx}. {status_icon} {change_type.upper()} - {semantic_badge}\n\n")
                
                # Категория и влияние
                if change.get('category'):
                    lines.append(f"**Категория:** {change['category']}\n")
                if change.get('impact'):
                    impact_icon = {'high': '🔴', 'medium': '🟡', 'low': '🟢'}.get(change['impact'], '⚪')
                    lines.append(f"**Влияние:** {impact_icon} {change['impact'].upper()}\n")
                lines.append("\n")
                
                # Анализ GPT-4
                if change.get('llm_summary'):
                    lines.append(f"**💡 Анализ GPT-4:**\n")
                    lines.append(f"> {change['llm_summary']}\n\n")
                
                # Тексты
                old_text = change.get('old_text', '')
                new_text = change.get('new_text', '')
                
                if change_type == 'modified':
                    if old_text:
                        if len(old_text) < 500:
                            lines.append(f"**❌ Было:**\n```\n{old_text}\n```\n\n")
                        else:
                            lines.append(f"**❌ Было:** _{len(old_text)} символов_\n\n")
                            lines.append(f"```\n{old_text[:300]}...\n```\n\n")
                    
                    if new_text:
                        if len(new_text) < 500:
                            lines.append(f"**✅ Стало:**\n```\n{new_text}\n```\n\n")
                        else:
                            lines.append(f"**✅ Стало:** _{len(new_text)} символов_\n\n")
                            lines.append(f"```\n{new_text[:300]}...\n```\n\n")
                    
                    # Детальный diff на уровне слов
                    if old_text and new_text and len(old_text) < 1000 and len(new_text) < 1000:
                        word_diff = self._get_inline_diff(old_text, new_text)
                        if word_diff:
                            lines.append(f"**🔬 Детали:**\n{word_diff}\n\n")
                
                elif change_type == 'added':
                    if new_text:
                        if len(new_text) < 500:
                            lines.append(f"**➕ Добавлено:**\n```\n{new_text}\n```\n\n")
                        else:
                            lines.append(f"**➕ Добавлено:** _{len(new_text)} символов_\n\n")
                            lines.append(f"```\n{new_text[:300]}...\n```\n\n")
                
                elif change_type == 'removed':
                    if old_text:
                        if len(old_text) < 500:
                            lines.append(f"**➖ Удалено:**\n```\n{old_text}\n```\n\n")
                        else:
                            lines.append(f"**➖ Удалено:** _{len(old_text)} символов_\n\n")
                            lines.append(f"```\n{old_text[:300]}...\n```\n\n")
                
                lines.append("---\n\n")
    
    markdown_text = "".join(lines)
    
    # Вывод
    print(markdown_text)
    
    # Сохранение
    if save_to:
        Path(save_to).write_text(markdown_text, encoding='utf-8')
        print(f"\n✅ Отчёт сохранён: {save_to}\n")

    def _get_inline_diff(self, old_text: str, new_text: str) -> str:
        """Получает inline diff с подсветкой изменений."""
        import difflib
        
        # Используем ndiff для посимвольного сравнения
        old_words = old_text.split()
        new_words = new_text.split()
        
        diff = list(difflib.ndiff(old_words, new_words))
        
        result = []
        for line in diff[:20]:  # Первые 20 изменений
            if line.startswith('- '):
                result.append(f"❌ `{line[2:]}`")
            elif line.startswith('+ '):
                result.append(f"✅ `{line[2:]}`")
        
        return " ".join(result) if result else ""


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Использование:")
        print(f"  python {sys.argv[0]} <case_id>")
        print(f"  python {sys.argv[0]} <case_id> --save diff.md")
        print()
        print("Пример:")
        print(f"  python {sys.argv[0]} 3b447bcc-1aa9-456e-89f8-7ce800ccfb27")
        print(f"  python {sys.argv[0]} 3b447bcc-1aa9-456e-89f8-7ce800ccfb27 --save changes.md")
        sys.exit(1)
    
    case_id = sys.argv[1]
    save_to = None
    
    if "--save" in sys.argv:
        idx = sys.argv.index("--save")
        if idx + 1 < len(sys.argv):
            save_to = sys.argv[idx + 1]
    
    diff_analyzer = get_detailed_diff(case_id, save_to)



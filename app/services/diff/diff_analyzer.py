"""Анализ различий между текстами."""

import difflib
from typing import Dict, List, Tuple

from diff_match_patch import diff_match_patch
from rapidfuzz import fuzz

from app.core.logging_config import get_logger

logger = get_logger(__name__)


class DiffAnalyzer:
    """Анализатор различий между двумя текстами."""

    def __init__(self):
        """Инициализация анализатора."""
        self.dmp = diff_match_patch()
        self.dmp.Diff_Timeout = 10.0  # 10 секунд таймаут

    def compare_texts(
        self,
        base_text: str,
        target_text: str,
    ) -> List[Dict]:
        """
        Сравнивает два текста и возвращает список изменений.
        
        Args:
            base_text: Исходный текст
            target_text: Новый текст
            
        Returns:
            Список изменений с метаданными
        """
        logger.info("Starting diff analysis")
        
        # Разбиваем тексты на абзацы
        base_paragraphs = self._split_into_paragraphs(base_text)
        target_paragraphs = self._split_into_paragraphs(target_text)
        
        # Сравниваем на уровне абзацев
        changes = self._compare_paragraphs(base_paragraphs, target_paragraphs)
        
        logger.info(f"Found {len(changes)} changes")
        return changes

    def _split_into_paragraphs(self, text: str) -> List[str]:
        """Разбивает текст на абзацы."""
        paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
        return paragraphs

    def _compare_paragraphs(
        self,
        base_paragraphs: List[str],
        target_paragraphs: List[str],
    ) -> List[Dict]:
        """Сравнивает абзацы и находит изменения."""
        changes = []
        
        # Используем SequenceMatcher для выравнивания абзацев
        matcher = difflib.SequenceMatcher(
            None,
            base_paragraphs,
            target_paragraphs,
            autojunk=False,
        )
        
        opcodes = matcher.get_opcodes()
        position = 0
        
        for tag, i1, i2, j1, j2 in opcodes:
            if tag == "equal":
                # Абзацы совпадают - пропускаем
                position += (i2 - i1)
                continue
            
            elif tag == "delete":
                # Абзацы удалены
                for i in range(i1, i2):
                    changes.append({
                        "position": position,
                        "change_type": "removed",
                        "old_text": base_paragraphs[i],
                        "new_text": None,
                        "context_before": self._get_context(base_paragraphs, i, -1),
                        "context_after": self._get_context(base_paragraphs, i, 1),
                    })
                    position += 1
            
            elif tag == "insert":
                # Абзацы добавлены
                for j in range(j1, j2):
                    changes.append({
                        "position": position,
                        "change_type": "added",
                        "old_text": None,
                        "new_text": target_paragraphs[j],
                        "context_before": self._get_context(target_paragraphs, j, -1),
                        "context_after": self._get_context(target_paragraphs, j, 1),
                    })
                    position += 1
            
            elif tag == "replace":
                # Абзацы изменены
                # Сравниваем попарно
                for base_idx in range(i1, i2):
                    old_para = base_paragraphs[base_idx]
                    
                    # Ищем наиболее похожий новый абзац
                    best_match = None
                    best_score = 0
                    
                    for target_idx in range(j1, j2):
                        new_para = target_paragraphs[target_idx]
                        score = fuzz.ratio(old_para, new_para)
                        
                        if score > best_score:
                            best_score = score
                            best_match = new_para
                    
                    # Если абзацы достаточно похожи - это модификация
                    if best_score > 30:  # Порог схожести
                        changes.append({
                            "position": position,
                            "change_type": "modified",
                            "old_text": old_para,
                            "new_text": best_match,
                            "similarity": best_score / 100.0,
                            "context_before": self._get_context(base_paragraphs, base_idx, -1),
                            "context_after": self._get_context(base_paragraphs, base_idx, 1),
                            "detailed_diff": self._get_detailed_diff(old_para, best_match),
                        })
                    else:
                        # Иначе - удаление старого и добавление нового
                        changes.append({
                            "position": position,
                            "change_type": "removed",
                            "old_text": old_para,
                            "new_text": None,
                            "context_before": self._get_context(base_paragraphs, base_idx, -1),
                            "context_after": self._get_context(base_paragraphs, base_idx, 1),
                        })
                        if best_match:
                            changes.append({
                                "position": position,
                                "change_type": "added",
                                "old_text": None,
                                "new_text": best_match,
                                "context_before": None,
                                "context_after": None,
                            })
                    
                    position += 1

        return changes

    def _get_context(
        self,
        paragraphs: List[str],
        index: int,
        offset: int,
        window: int = 1,
    ) -> str:
        """Получает контекст вокруг абзаца."""
        context_paragraphs = []
        
        for i in range(window):
            idx = index + offset * (i + 1)
            if 0 <= idx < len(paragraphs):
                context_paragraphs.append(paragraphs[idx])
        
        if offset < 0:
            context_paragraphs.reverse()
        
        return " ".join(context_paragraphs) if context_paragraphs else None

    def _get_detailed_diff(self, old_text: str, new_text: str) -> List[Dict]:
        """
        Получает детальный diff на уровне слов/символов.
        
        Returns:
            Список операций diff
        """
        diffs = self.dmp.diff_main(old_text, new_text)
        self.dmp.diff_cleanupSemantic(diffs)
        
        detailed = []
        for op, text in diffs:
            if op == -1:  # DELETE
                detailed.append({"type": "delete", "text": text})
            elif op == 1:  # INSERT
                detailed.append({"type": "insert", "text": text})
            # op == 0 (EQUAL) пропускаем для краткости
        
        return detailed

    def filter_noise(self, changes: List[Dict]) -> List[Dict]:
        """
        Фильтрует незначительные изменения (шум).
        
        Убирает изменения, которые касаются только:
        - Пробелов и переносов строк
        - Регистра букв
        - Пунктуации
        
        Args:
            changes: Список изменений
            
        Returns:
            Отфильтрованный список
        """
        filtered = []
        
        for change in changes:
            if self._is_noise(change):
                logger.debug(f"Filtered noise change at position {change['position']}")
                continue
            filtered.append(change)
        
        return filtered

    def _is_noise(self, change: Dict) -> bool:
        """Проверяет, является ли изменение шумом."""
        old = change.get("old_text", "") or ""
        new = change.get("new_text", "") or ""
        
        # Нормализуем для сравнения
        old_normalized = self._normalize_for_noise_check(old)
        new_normalized = self._normalize_for_noise_check(new)
        
        # Если после нормализации тексты идентичны - это шум
        return old_normalized == new_normalized

    def _normalize_for_noise_check(self, text: str) -> str:
        """Нормализует текст для проверки на шум."""
        import re
        
        # Приводим к нижнему регистру
        text = text.lower()
        
        # Убираем все пробельные символы
        text = re.sub(r"\s+", "", text)
        
        # Убираем знаки препинания
        text = re.sub(r"[^\w\s]", "", text)
        
        return text

    def get_statistics(self, changes: List[Dict]) -> Dict:
        """
        Получает статистику по изменениям.
        
        Args:
            changes: Список изменений
            
        Returns:
            Словарь со статистикой
        """
        stats = {
            "total_changes": len(changes),
            "added": 0,
            "removed": 0,
            "modified": 0,
        }
        
        for change in changes:
            change_type = change["change_type"]
            if change_type in stats:
                stats[change_type] += 1
        
        return stats


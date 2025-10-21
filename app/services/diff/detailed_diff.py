"""Детальный diff-анализ на уровне предложений и абзацев."""

import difflib
from typing import Dict, List

from app.core.logging_config import get_logger

logger = get_logger(__name__)


class DetailedDiffAnalyzer:
    """Анализатор для получения детального списка изменений."""

    def get_detailed_changes(
        self,
        base_text: str,
        target_text: str,
    ) -> List[Dict]:
        """
        Получает детальный список изменений по предложениям.
        
        Args:
            base_text: Исходный текст
            target_text: Новый текст
            
        Returns:
            Список детальных изменений
        """
        # Разбиваем на предложения
        base_sentences = self._split_into_sentences(base_text)
        target_sentences = self._split_into_sentences(target_text)
        
        # Используем SequenceMatcher для поиска различий
        matcher = difflib.SequenceMatcher(None, base_sentences, target_sentences)
        
        changes = []
        change_number = 1
        
        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            if tag == 'equal':
                # Предложения совпадают - пропускаем
                continue
            
            elif tag == 'delete':
                # Предложения удалены
                for idx in range(i1, i2):
                    changes.append({
                        'number': change_number,
                        'type': 'removed',
                        'status': '➖ УДАЛЕНО',
                        'text': base_sentences[idx],
                        'line_number': idx + 1,
                        'context': self._get_sentence_context(base_sentences, idx),
                    })
                    change_number += 1
            
            elif tag == 'insert':
                # Предложения добавлены
                for idx in range(j1, j2):
                    changes.append({
                        'number': change_number,
                        'type': 'added',
                        'status': '➕ ДОБАВЛЕНО',
                        'text': target_sentences[idx],
                        'line_number': idx + 1,
                        'context': self._get_sentence_context(target_sentences, idx),
                    })
                    change_number += 1
            
            elif tag == 'replace':
                # Предложения изменены
                for old_idx in range(i1, i2):
                    old_sentence = base_sentences[old_idx]
                    
                    # Ищем наиболее похожее новое предложение
                    best_match_idx = None
                    best_ratio = 0
                    
                    for new_idx in range(j1, j2):
                        ratio = difflib.SequenceMatcher(
                            None, old_sentence, target_sentences[new_idx]
                        ).ratio()
                        if ratio > best_ratio:
                            best_ratio = ratio
                            best_match_idx = new_idx
                    
                    if best_match_idx is not None and best_ratio > 0.3:
                        # Это модификация
                        new_sentence = target_sentences[best_match_idx]
                        word_changes = self._get_word_diff(old_sentence, new_sentence)
                        
                        changes.append({
                            'number': change_number,
                            'type': 'modified',
                            'status': '✏️ ИЗМЕНЕНО',
                            'old_text': old_sentence,
                            'new_text': new_sentence,
                            'line_number': old_idx + 1,
                            'similarity': best_ratio,
                            'word_changes': word_changes,
                            'context': self._get_sentence_context(base_sentences, old_idx),
                        })
                    else:
                        # Это удаление + добавление
                        changes.append({
                            'number': change_number,
                            'type': 'removed',
                            'status': '➖ УДАЛЕНО',
                            'text': old_sentence,
                            'line_number': old_idx + 1,
                            'context': self._get_sentence_context(base_sentences, old_idx),
                        })
                    
                    change_number += 1
        
        return changes

    def _split_into_sentences(self, text: str) -> List[str]:
        """Разбивает текст на предложения."""
        import re
        
        # Нормализуем текст
        text = text.replace('\n\n', ' [PARAGRAPH] ')
        text = text.replace('\n', ' ')
        
        # Паттерн для разбиения на предложения
        # Учитываем сокращения и числа
        pattern = r'(?<!\w\.\w.)(?<![A-ZА-Я][а-яa-z]\.)(?<=\.|\?|\!|\[PARAGRAPH\])\s+'
        
        sentences = re.split(pattern, text)
        sentences = [s.replace('[PARAGRAPH]', '').strip() for s in sentences if s.strip()]
        
        return sentences

    def _get_sentence_context(self, sentences: List[str], index: int, window: int = 1) -> Dict:
        """Получает контекст вокруг предложения."""
        context = {}
        
        if index > 0:
            context['before'] = sentences[index - 1][:100] + '...' if len(sentences[index - 1]) > 100 else sentences[index - 1]
        
        if index < len(sentences) - 1:
            context['after'] = sentences[index + 1][:100] + '...' if len(sentences[index + 1]) > 100 else sentences[index + 1]
        
        return context

    def _get_word_diff(self, old_text: str, new_text: str) -> List[Dict]:
        """Получает различия на уровне слов."""
        old_words = old_text.split()
        new_words = new_text.split()
        
        matcher = difflib.SequenceMatcher(None, old_words, new_words)
        
        word_changes = []
        
        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            if tag == 'delete':
                word_changes.append({
                    'type': 'removed',
                    'words': ' '.join(old_words[i1:i2])
                })
            elif tag == 'insert':
                word_changes.append({
                    'type': 'added',
                    'words': ' '.join(new_words[j1:j2])
                })
            elif tag == 'replace':
                word_changes.append({
                    'type': 'changed',
                    'old_words': ' '.join(old_words[i1:i2]),
                    'new_words': ' '.join(new_words[j1:j2])
                })
        
        return word_changes



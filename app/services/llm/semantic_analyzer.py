"""Семантический анализ изменений с использованием LLM."""

import json
from typing import Dict, List, Optional

from openai import AsyncOpenAI

from app.core.config import settings
from app.core.logging_config import get_logger

logger = get_logger(__name__)


class SemanticAnalyzer:
    """Анализатор семантических изменений с использованием LLM."""

    def __init__(self):
        """Инициализация клиента OpenAI."""
        if settings.OPENAI_API_KEY:
            self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        else:
            logger.warning("OpenAI API key not set, semantic analysis will be unavailable")
            self.client = None

    async def analyze_change(self, change: Dict) -> Dict:
        """
        Анализирует одно изменение и определяет его семантическую значимость.
        
        Args:
            change: Словарь с информацией об изменении
            
        Returns:
            Обогащённая информация об изменении
        """
        if not self.client:
            return self._fallback_analysis(change)

        old_text = change.get("old_text", "")
        new_text = change.get("new_text", "")
        change_type = change["change_type"]

        # Формируем промпт
        prompt = self._build_analysis_prompt(old_text, new_text, change_type)

        try:
            response = await self.client.chat.completions.create(
                model=settings.OPENAI_MODEL,
                messages=[
                    {
                        "role": "system",
                        "content": self._get_system_prompt(),
                    },
                    {
                        "role": "user",
                        "content": prompt,
                    }
                ],
                temperature=settings.OPENAI_TEMPERATURE,
                max_tokens=500,
                response_format={"type": "json_object"},
            )

            # Парсим ответ
            result = json.loads(response.choices[0].message.content)
            
            return {
                **change,
                "is_semantic_change": result.get("is_semantic_change", True),
                "category": result.get("category", "other"),
                "impact": result.get("impact", "medium"),
                "llm_summary": result.get("summary", ""),
                "llm_reasoning": result.get("reasoning", ""),
            }

        except Exception as e:
            logger.error(f"Error analyzing change with LLM: {e}")
            return self._fallback_analysis(change)

    def _get_system_prompt(self) -> str:
        """Возвращает системный промпт для LLM."""
        return """Ты - эксперт по анализу юридических и деловых документов. 
Твоя задача - определить, является ли изменение в документе семантически значимым, 
то есть меняет ли оно фактический смысл текста.

Игнорируй косметические изменения:
- Исправления опечаток
- Изменения форматирования
- Перефразирование без изменения смысла
- Изменения пунктуации, которые не влияют на смысл

Обращай внимание на смысловые изменения:
- Изменения сроков, дат, периодов
- Изменения денежных сумм, процентов, количеств
- Изменения обязательств сторон
- Изменения условий выполнения
- Добавление или удаление важных пунктов
- Изменения, влияющие на права и обязанности

Отвечай в формате JSON со следующими полями:
{
  "is_semantic_change": true/false,
  "category": "dates|obligations|financial|conditions|parties|technical|other",
  "impact": "low|medium|high",
  "summary": "краткое описание изменения на русском языке",
  "reasoning": "объяснение, почему это изменение значимо или нет"
}"""

    def _build_analysis_prompt(
        self,
        old_text: Optional[str],
        new_text: Optional[str],
        change_type: str,
    ) -> str:
        """Формирует промпт для анализа изменения."""
        if change_type == "added":
            return f"""Добавлен новый фрагмент текста:

НОВЫЙ ТЕКСТ:
{new_text}

Проанализируй, является ли это добавление семантически значимым."""

        elif change_type == "removed":
            return f"""Удалён фрагмент текста:

УДАЛЁННЫЙ ТЕКСТ:
{old_text}

Проанализируй, является ли это удаление семантически значимым."""

        else:  # modified
            return f"""Изменён фрагмент текста:

СТАРЫЙ ТЕКСТ:
{old_text}

НОВЫЙ ТЕКСТ:
{new_text}

Проанализируй, является ли это изменение семантически значимым."""

    def _fallback_analysis(self, change: Dict) -> Dict:
        """
        Резервный анализ без LLM (простая эвристика).
        
        Используется, если LLM недоступен.
        """
        old_text = (change.get("old_text") or "").lower()
        new_text = (change.get("new_text") or "").lower()

        # Простые правила для определения важности
        is_semantic = False
        category = "other"
        impact = "medium"

        # Проверяем на числовые изменения
        if self._contains_numbers(old_text) or self._contains_numbers(new_text):
            if self._numbers_changed(old_text, new_text):
                is_semantic = True
                category = "financial"
                impact = "high"

        # Проверяем на изменения дат
        if self._contains_dates(old_text) or self._contains_dates(new_text):
            is_semantic = True
            category = "dates"
            impact = "high"

        # Проверяем ключевые слова обязательств
        obligation_keywords = ["обязан", "должен", "вправе", "имеет право", "обязуется"]
        if any(kw in old_text or kw in new_text for kw in obligation_keywords):
            is_semantic = True
            category = "obligations"
            impact = "high"

        return {
            **change,
            "is_semantic_change": is_semantic,
            "category": category,
            "impact": impact,
            "llm_summary": "Анализ выполнен эвристическим методом (LLM недоступен)",
            "llm_reasoning": "Использованы простые правила для определения важности",
        }

    def _contains_numbers(self, text: str) -> bool:
        """Проверяет, содержит ли текст числа."""
        import re
        return bool(re.search(r"\d+", text))

    def _numbers_changed(self, old_text: str, new_text: str) -> bool:
        """Проверяет, изменились ли числа в тексте."""
        import re
        old_numbers = set(re.findall(r"\d+(?:\.\d+)?", old_text))
        new_numbers = set(re.findall(r"\d+(?:\.\d+)?", new_text))
        return old_numbers != new_numbers

    def _contains_dates(self, text: str) -> bool:
        """Проверяет, содержит ли текст даты."""
        import re
        # Простой паттерн для дат
        date_patterns = [
            r"\d{1,2}\.\d{1,2}\.\d{2,4}",  # DD.MM.YYYY
            r"\d{1,2}/\d{1,2}/\d{2,4}",    # DD/MM/YYYY
            r"\d{4}-\d{2}-\d{2}",          # YYYY-MM-DD
        ]
        return any(re.search(pattern, text) for pattern in date_patterns)

    async def analyze_batch(self, changes: List[Dict], batch_size: int = 5) -> List[Dict]:
        """
        Анализирует группу изменений пакетами.
        
        Args:
            changes: Список изменений
            batch_size: Размер пакета
            
        Returns:
            Список обогащённых изменений
        """
        results = []
        
        for i in range(0, len(changes), batch_size):
            batch = changes[i:i + batch_size]
            
            # Анализируем параллельно
            import asyncio
            batch_results = await asyncio.gather(
                *[self.analyze_change(change) for change in batch],
                return_exceptions=True,
            )
            
            # Обрабатываем результаты
            for result in batch_results:
                if isinstance(result, Exception):
                    logger.error(f"Error in batch analysis: {result}")
                    continue
                results.append(result)
        
        return results

    async def generate_summary(self, changes: List[Dict]) -> str:
        """
        Генерирует общую сводку по всем изменениям.
        
        Args:
            changes: Список проанализированных изменений
            
        Returns:
            Текстовая сводка
        """
        if not self.client:
            return self._fallback_summary(changes)

        # Фильтруем только семантические изменения
        semantic_changes = [c for c in changes if c.get("is_semantic_change", False)]
        
        if not semantic_changes:
            return "Семантических изменений не обнаружено. Все изменения носят технический характер."

        # Формируем краткое описание изменений
        changes_description = []
        for idx, change in enumerate(semantic_changes[:10], 1):  # Берём первые 10
            category = change.get("category", "прочее")
            impact = change.get("impact", "средний")
            summary = change.get("llm_summary", "")
            changes_description.append(f"{idx}. [{category}, {impact}] {summary}")

        prompt = f"""Проанализируй следующие изменения в документе и составь краткую сводку 
(2-3 предложения) о том, что изменилось в целом:

Всего изменений: {len(changes)}
Семантически значимых: {len(semantic_changes)}

Изменения:
{chr(10).join(changes_description)}

Сводка должна быть на русском языке и отражать основные тенденции изменений."""

        try:
            response = await self.client.chat.completions.create(
                model=settings.OPENAI_MODEL,
                messages=[
                    {
                        "role": "system",
                        "content": "Ты - эксперт по анализу документов. Составь краткую сводку изменений.",
                    },
                    {
                        "role": "user",
                        "content": prompt,
                    }
                ],
                temperature=0.3,
                max_tokens=300,
            )

            return response.choices[0].message.content.strip()

        except Exception as e:
            logger.error(f"Error generating summary: {e}")
            return self._fallback_summary(changes)

    def _fallback_summary(self, changes: List[Dict]) -> str:
        """Генерирует простую сводку без LLM."""
        semantic_changes = [c for c in changes if c.get("is_semantic_change", False)]
        
        if not semantic_changes:
            return "Семантических изменений не обнаружено."

        # Подсчитываем по категориям
        categories = {}
        for change in semantic_changes:
            cat = change.get("category", "other")
            categories[cat] = categories.get(cat, 0) + 1

        summary_parts = [
            f"Обнаружено {len(semantic_changes)} семантически значимых изменений из {len(changes)} общих."
        ]

        if categories:
            cats_str = ", ".join([f"{cat}: {count}" for cat, count in categories.items()])
            summary_parts.append(f"По категориям: {cats_str}.")

        return " ".join(summary_parts)



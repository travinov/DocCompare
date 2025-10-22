"""API endpoint для экспорта детальных отчётов."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse, PlainTextResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.logging_config import get_logger
from app.models.comparison import ComparisonCase, ComparisonDocument
from app.storage import get_storage

logger = get_logger(__name__)

router = APIRouter()


@router.get("/{case_id}/export/detailed-diff")
async def export_detailed_diff(
    case_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """
    Генерирует и возвращает детальный diff в Markdown формате.
    
    Файл сохраняется в папку reports/{case_id}/detailed_diff.md
    """
    from sqlalchemy import select
    import re
    import difflib
    
    # Получаем кейс и документы
    case = await db.get(ComparisonCase, case_id)
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    
    stmt = select(ComparisonDocument).where(ComparisonDocument.case_id == case_id)
    result = await db.execute(stmt)
    documents = result.scalars().all()
    
    base_doc = next((d for d in documents if d.document_type == 'base'), None)
    target_doc = next((d for d in documents if d.document_type == 'target'), None)
    
    if not base_doc or not target_doc:
        raise HTTPException(status_code=404, detail="Documents not found")
    
    # Формируем Markdown отчёт
    lines = []
    
    lines.append(f"# 📋 Детальный Diff-отчёт\n\n")
    lines.append(f"**Case ID:** `{case_id}`\n\n")
    
    lines.append("## 📄 Сравниваемые документы\n\n")
    lines.append(f"**📕 Базовый:** {base_doc.original_filename}\n")
    lines.append(f"**📗 Новый:** {target_doc.original_filename}\n\n")
    
    lines.append("## 📊 Статистика\n\n")
    lines.append(f"- Статус: `{case.status}`\n")
    if case.processing_time:
        lines.append(f"- Время обработки: {case.processing_time:.2f} сек.\n")
    lines.append(f"- Всего изменений: **{case.total_changes}**\n")
    lines.append(f"- 🔴 Семантических: **{case.semantic_changes_count}**\n")
    lines.append(f"- 🟡 Технических: **{case.technical_changes_count}**\n")
    if case.overall_impact:
        lines.append(f"- Влияние: **{case.overall_impact.upper()}**\n")
    lines.append("\n")
    
    if case.summary:
        lines.append("## 💡 Общая сводка GPT-4\n\n")
        lines.append(f"> {case.summary}\n\n")
        lines.append("---\n\n")
    
    lines.append("## 🔍 Детальный нумерованный список изменений\n\n")
    
    # Получаем нормализованные тексты
    base_text = base_doc.normalized_text or base_doc.extracted_text or ""
    target_text = target_doc.normalized_text or target_doc.extracted_text or ""
    
    if base_text and target_text:
        # Разбиваем на предложения
        def split_sentences(text):
            sentences = re.split(r'(?<=[.!?])\s+', text)
            return [s.strip() for s in sentences if s.strip()]
        
        base_sentences = split_sentences(base_text)
        target_sentences = split_sentences(target_text)
        
        # Получаем diff
        matcher = difflib.SequenceMatcher(None, base_sentences, target_sentences)
        
        change_num = 1
        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            if tag == 'equal':
                continue
            
            if tag == 'delete':
                for i in range(i1, i2):
                    lines.append(f"### {change_num}. ➖ УДАЛЕНО\n\n")
                    text = base_sentences[i]
                    lines.append(f"```\n{text}\n```\n\n")
                    lines.append("---\n\n")
                    change_num += 1
            
            elif tag == 'insert':
                for j in range(j1, j2):
                    lines.append(f"### {change_num}. ➕ ДОБАВЛЕНО\n\n")
                    text = target_sentences[j]
                    lines.append(f"```\n{text}\n```\n\n")
                    lines.append("---\n\n")
                    change_num += 1
            
            elif tag == 'replace':
                for i in range(i1, min(i2, i1 + (j2-j1))):
                    old_sent = base_sentences[i] if i < len(base_sentences) else ""
                    j_idx = j1 + (i - i1)
                    new_sent = target_sentences[j_idx] if j_idx < len(target_sentences) else ""
                    
                    if old_sent or new_sent:
                        lines.append(f"### {change_num}. ✏️ ИЗМЕНЕНО\n\n")
                        if old_sent:
                            lines.append(f"**❌ Было:**\n```\n{old_sent}\n```\n\n")
                        if new_sent:
                            lines.append(f"**✅ Стало:**\n```\n{new_sent}\n```\n\n")
                        lines.append("---\n\n")
                        change_num += 1
    else:
        lines.append("_Текст не извлечён_\n")
    
    lines.append(f"\n**Всего изменений:** {change_num - 1}\n")
    lines.append(f"\n---\n\n_Создано системой DocCompare_\n")
    
    markdown_content = "".join(lines)
    
    # Сохраняем в MinIO в папку case_id
    storage = get_storage()
    file_content = markdown_content.encode('utf-8')
    
    object_name = f"reports/{case_id}/detailed_diff.md"
    storage.upload_file(
        file_data=__import__('io').BytesIO(file_content),
        object_name=object_name,
        content_type="text/markdown",
    )
    
    logger.info(f"Generated detailed diff for case {case_id}")
    
    # Возвращаем файл для скачивания
    return PlainTextResponse(
        content=markdown_content,
        media_type="text/markdown; charset=utf-8",
        headers={
            "Content-Disposition": f"attachment; filename=detailed_diff_{case_id}.md"
        }
    )


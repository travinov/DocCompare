"""API endpoint для получения детального diff."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.logging_config import get_logger
from app.models.comparison import ComparisonCase, ComparisonDocument
from app.services.diff.detailed_diff import DetailedDiffAnalyzer

logger = get_logger(__name__)

router = APIRouter()


@router.get("/{case_id}/detailed-diff")
async def get_detailed_diff(
    case_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """
    Получает детальный diff на уровне предложений.
    
    Возвращает нумерованный список всех изменений с указанием:
    - Номер изменения
    - Тип (добавлено/удалено/изменено)
    - Старый и новый текст
    - Детали на уровне слов
    """
    from sqlalchemy import select
    
    # Получаем кейс
    case = await db.get(ComparisonCase, case_id)
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    
    # Получаем документы
    stmt = select(ComparisonDocument).where(
        ComparisonDocument.case_id == case_id
    )
    result = await db.execute(stmt)
    documents = result.scalars().all()
    
    base_doc = next((d for d in documents if d.document_type == 'base'), None)
    target_doc = next((d for d in documents if d.document_type == 'target'), None)
    
    if not base_doc or not target_doc:
        raise HTTPException(status_code=404, detail="Documents not found")
    
    if not base_doc.normalized_text or not target_doc.normalized_text:
        raise HTTPException(status_code=400, detail="Text not extracted yet")
    
    # Выполняем детальный анализ
    analyzer = DetailedDiffAnalyzer()
    detailed_changes = analyzer.get_detailed_changes(
        base_doc.normalized_text,
        target_doc.normalized_text,
    )
    
    return {
        "case_id": str(case_id),
        "total_changes": len(detailed_changes),
        "changes": detailed_changes,
        "summary": {
            "added": len([c for c in detailed_changes if c['type'] == 'added']),
            "removed": len([c for c in detailed_changes if c['type'] == 'removed']),
            "modified": len([c for c in detailed_changes if c['type'] == 'modified']),
        }
    }


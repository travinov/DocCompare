"""API endpoints для сравнения документов."""

import asyncio
import io
import time
from pathlib import Path
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.logging_config import get_logger
from app.models.comparison import ComparisonCase, ComparisonChange, ComparisonDocument
from app.schemas.comparison import CaseResponse, ChangeResponse, ReportResponse
from app.services.diff import DiffAnalyzer
from app.services.extraction import TextExtractor
from app.services.llm import SemanticAnalyzer
from app.services.reports import ReportGenerator
from app.storage import get_storage

logger = get_logger(__name__)

router = APIRouter()


@router.post("/", response_model=CaseResponse)
async def compare_documents(
    base_file: UploadFile = File(..., description="Базовая версия документа"),
    target_file: UploadFile = File(..., description="Новая версия документа"),
    db: AsyncSession = Depends(get_db),
):
    """
    Сравнивает два документа и запускает анализ.
    
    Поддерживаемые форматы: DOC, DOCX, PDF
    """
    start_time = time.time()
    
    try:
        # Создаём кейс
        case = ComparisonCase(status="pending")
        db.add(case)
        await db.flush()
        
        logger.info(f"Created comparison case: {case.id}")
        
        # Загружаем файлы в хранилище
        storage = get_storage()
        
        # Базовый документ
        base_content = await base_file.read()
        base_path = storage.upload_document(
            case.id,
            "base",
            io.BytesIO(base_content),
            base_file.filename,
        )
        
        # Целевой документ
        target_content = await target_file.read()
        target_path = storage.upload_document(
            case.id,
            "target",
            io.BytesIO(target_content),
            target_file.filename,
        )
        
        # Создаём записи документов
        base_doc = ComparisonDocument(
            case_id=case.id,
            document_type="base",
            original_filename=base_file.filename,
            file_format=Path(base_file.filename).suffix.lstrip('.').lower(),
            file_size=len(base_content),
            storage_path=base_path,
        )
        
        target_doc = ComparisonDocument(
            case_id=case.id,
            document_type="target",
            original_filename=target_file.filename,
            file_format=Path(target_file.filename).suffix.lstrip('.').lower(),
            file_size=len(target_content),
            storage_path=target_path,
        )
        
        db.add(base_doc)
        db.add(target_doc)
        await db.commit()
        
        logger.info(f"Uploaded documents for case {case.id}")
        
        # Запускаем обработку асинхронно
        asyncio.create_task(
            process_comparison(case.id, base_doc.id, target_doc.id)
        )
        
        # Возвращаем начальный статус
        await db.refresh(case)
        return case
        
    except Exception as e:
        logger.error(f"Error creating comparison: {e}")
        raise HTTPException(status_code=500, detail=str(e))


async def process_comparison(
    case_id: UUID,
    base_doc_id: UUID,
    target_doc_id: UUID,
):
    """Фоновая обработка сравнения документов."""
    from app.core.database import async_session_maker
    
    async with async_session_maker() as db:
        try:
            start_time = time.time()
            
            # Получаем кейс и документы
            case = await db.get(ComparisonCase, case_id)
            base_doc = await db.get(ComparisonDocument, base_doc_id)
            target_doc = await db.get(ComparisonDocument, target_doc_id)
            
            # Этап 1: Извлечение текста
            logger.info(f"[{case_id}] Step 1: Extracting text")
            case.status = "extracting"
            await db.commit()
            
            storage = get_storage()
            extractor = TextExtractor()
            
            # Извлекаем текст из базового документа
            base_stream = storage.get_file_stream(
                base_doc.storage_path.split('/', 1)[1]
            )
            base_text, base_structure, base_is_scanned, base_ocr_conf = \
                extractor.extract(base_stream, base_doc.file_format, base_doc.original_filename)
            
            base_doc.extracted_text = base_text
            base_doc.normalized_text = extractor.normalize_text(base_text)
            base_doc.structure = base_structure
            base_doc.is_scanned = base_is_scanned
            base_doc.ocr_confidence = base_ocr_conf
            
            # Извлекаем текст из целевого документа
            target_stream = storage.get_file_stream(
                target_doc.storage_path.split('/', 1)[1]
            )
            target_text, target_structure, target_is_scanned, target_ocr_conf = \
                extractor.extract(target_stream, target_doc.file_format, target_doc.original_filename)
            
            target_doc.extracted_text = target_text
            target_doc.normalized_text = extractor.normalize_text(target_text)
            target_doc.structure = target_structure
            target_doc.is_scanned = target_is_scanned
            target_doc.ocr_confidence = target_ocr_conf
            
            await db.commit()
            logger.info(f"[{case_id}] Text extraction completed")
            
            # Этап 2: Diff анализ
            logger.info(f"[{case_id}] Step 2: Diff analysis")
            case.status = "diffing"
            await db.commit()
            
            diff_analyzer = DiffAnalyzer()
            changes = diff_analyzer.compare_texts(
                base_doc.normalized_text,
                target_doc.normalized_text,
            )
            
            # Фильтруем шум
            changes = diff_analyzer.filter_noise(changes)
            
            logger.info(f"[{case_id}] Found {len(changes)} changes")
            
            # Этап 3: Семантический анализ
            logger.info(f"[{case_id}] Step 3: Semantic analysis")
            case.status = "analyzing"
            await db.commit()
            
            semantic_analyzer = SemanticAnalyzer()
            analyzed_changes = await semantic_analyzer.analyze_batch(changes)
            
            # Сохраняем изменения в БД
            for change_data in analyzed_changes:
                change = ComparisonChange(
                    case_id=case.id,
                    position=change_data["position"],
                    change_type=change_data["change_type"],
                    old_text=change_data.get("old_text"),
                    new_text=change_data.get("new_text"),
                    context_before=change_data.get("context_before"),
                    context_after=change_data.get("context_after"),
                    is_semantic_change=change_data.get("is_semantic_change", False),
                    category=change_data.get("category"),
                    impact=change_data.get("impact"),
                    llm_summary=change_data.get("llm_summary"),
                    llm_reasoning=change_data.get("llm_reasoning"),
                    similarity_score=change_data.get("similarity"),
                )
                db.add(change)
            
            await db.commit()
            
            # Генерируем общую сводку
            summary = await semantic_analyzer.generate_summary(analyzed_changes)
            case.summary = summary
            
            # Подсчитываем статистику
            semantic_count = sum(1 for c in analyzed_changes if c.get("is_semantic_change"))
            case.total_changes = len(analyzed_changes)
            case.semantic_changes_count = semantic_count
            case.technical_changes_count = len(analyzed_changes) - semantic_count
            
            # Определяем общее влияние
            high_impact_count = sum(1 for c in analyzed_changes if c.get("impact") == "high")
            if high_impact_count > 0:
                case.overall_impact = "high"
            elif semantic_count > 0:
                case.overall_impact = "medium"
            else:
                case.overall_impact = "low"
            
            await db.commit()
            logger.info(f"[{case_id}] Semantic analysis completed")
            
            # Этап 4: Генерация отчётов
            logger.info(f"[{case_id}] Step 4: Generating reports")
            case.status = "generating"
            await db.commit()
            
            report_gen = ReportGenerator()
            
            case_data = {
                "status": case.status,
                "processing_time": time.time() - start_time,
            }
            
            # HTML отчёт
            html_report = report_gen.generate_html_report(
                case.id,
                case_data,
                analyzed_changes,
                summary,
            )
            html_path = storage.upload_report(case.id, "html", html_report.encode('utf-8'))
            case.html_report_path = html_path
            
            # JSON отчёт
            json_report = report_gen.generate_json_report(
                case.id,
                case_data,
                analyzed_changes,
                summary,
            )
            json_path = storage.upload_report(case.id, "json", json_report.encode('utf-8'))
            case.json_report_path = json_path
            
            # PDF отчёт
            try:
                pdf_report = report_gen.generate_pdf_report(
                    case.id,
                    case_data,
                    analyzed_changes,
                    summary,
                )
                pdf_path = storage.upload_report(case.id, "pdf", pdf_report)
                case.pdf_report_path = pdf_path
            except Exception as e:
                logger.error(f"[{case_id}] Error generating PDF: {e}")
            
            # Завершаем
            case.status = "completed"
            case.processing_time = time.time() - start_time
            await db.commit()
            
            logger.info(f"[{case_id}] Processing completed in {case.processing_time:.2f}s")
            
        except Exception as e:
            logger.error(f"[{case_id}] Error processing comparison: {e}", exc_info=True)
            case.status = "failed"
            case.error_message = str(e)
            await db.commit()


@router.get("/{case_id}", response_model=CaseResponse)
async def get_case(
    case_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Получает информацию о кейсе сравнения."""
    from sqlalchemy import select
    from sqlalchemy.orm import selectinload
    
    stmt = select(ComparisonCase).where(
        ComparisonCase.id == case_id
    ).options(
        selectinload(ComparisonCase.documents),
        selectinload(ComparisonCase.changes),
    )
    
    result = await db.execute(stmt)
    case = result.scalar_one_or_none()
    
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    
    return case


@router.get("/{case_id}/changes", response_model=List[ChangeResponse])
async def get_changes(
    case_id: UUID,
    semantic_only: bool = False,
    db: AsyncSession = Depends(get_db),
):
    """Получает список изменений для кейса."""
    from sqlalchemy import select
    
    stmt = select(ComparisonChange).where(
        ComparisonChange.case_id == case_id
    ).order_by(ComparisonChange.position)
    
    if semantic_only:
        stmt = stmt.where(ComparisonChange.is_semantic_change == True)
    
    result = await db.execute(stmt)
    changes = result.scalars().all()
    
    return changes


@router.get("/{case_id}/reports", response_model=ReportResponse)
async def get_reports(
    case_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Получает ссылки на отчёты."""
    case = await db.get(ComparisonCase, case_id)
    
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    
    storage = get_storage()
    
    response = ReportResponse(case_id=case.id)
    
    if case.html_report_path:
        response.html_url = storage.get_presigned_url(
            case.html_report_path.split('/', 1)[1]
        )
    
    if case.pdf_report_path:
        response.pdf_url = storage.get_presigned_url(
            case.pdf_report_path.split('/', 1)[1]
        )
    
    if case.json_report_path:
        response.json_url = storage.get_presigned_url(
            case.json_report_path.split('/', 1)[1]
        )
    
    return response


@router.get("/{case_id}/report/html", response_class=HTMLResponse)
async def get_html_report(
    case_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Возвращает HTML отчёт напрямую."""
    case = await db.get(ComparisonCase, case_id)
    
    if not case or not case.html_report_path:
        raise HTTPException(status_code=404, detail="Report not found")
    
    storage = get_storage()
    html_bytes = storage.download_file(case.html_report_path.split('/', 1)[1])
    
    return HTMLResponse(content=html_bytes.decode('utf-8'))


@router.delete("/{case_id}")
async def delete_case(
    case_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Удаляет кейс и все связанные файлы."""
    case = await db.get(ComparisonCase, case_id)
    
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    
    # Удаляем файлы из хранилища
    storage = get_storage()
    storage.delete_case_files(case_id)
    
    # Удаляем из БД
    await db.delete(case)
    await db.commit()
    
    logger.info(f"Deleted case {case_id}")
    
    return {"status": "deleted", "case_id": str(case_id)}


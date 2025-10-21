"""Схемы для API сравнения документов."""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class ComparisonStatus(str, Enum):
    """Статус обработки кейса."""
    PENDING = "pending"
    EXTRACTING = "extracting"
    DIFFING = "diffing"
    ANALYZING = "analyzing"
    GENERATING = "generating"
    COMPLETED = "completed"
    FAILED = "failed"


class DocumentType(str, Enum):
    """Тип документа в сравнении."""
    BASE = "base"
    TARGET = "target"


class ChangeType(str, Enum):
    """Тип технического изменения."""
    ADDED = "added"
    REMOVED = "removed"
    MODIFIED = "modified"


class ChangeCategory(str, Enum):
    """Категория семантического изменения."""
    DATES = "dates"
    OBLIGATIONS = "obligations"
    FINANCIAL = "financial"
    CONDITIONS = "conditions"
    PARTIES = "parties"
    TECHNICAL = "technical"
    OTHER = "other"


class ImpactLevel(str, Enum):
    """Уровень влияния изменения."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class DocumentResponse(BaseModel):
    """Информация о документе."""
    
    id: UUID
    document_type: DocumentType
    original_filename: str
    file_format: str
    file_size: int
    is_scanned: bool = False
    ocr_confidence: Optional[float] = None
    created_at: datetime

    class Config:
        from_attributes = True


class ChangeResponse(BaseModel):
    """Информация об изменении."""
    
    id: UUID
    position: int
    section: Optional[str] = None
    change_type: ChangeType
    old_text: Optional[str] = None
    new_text: Optional[str] = None
    is_semantic_change: bool
    category: Optional[ChangeCategory] = None
    impact: Optional[ImpactLevel] = None
    llm_summary: Optional[str] = None
    similarity_score: Optional[float] = None

    class Config:
        from_attributes = True


class CaseResponse(BaseModel):
    """Информация о кейсе сравнения."""
    
    id: UUID
    status: ComparisonStatus
    created_at: datetime
    updated_at: Optional[datetime] = None
    total_changes: int = 0
    semantic_changes_count: int = 0
    technical_changes_count: int = 0
    overall_impact: Optional[ImpactLevel] = None
    summary: Optional[str] = None
    processing_time: Optional[float] = None
    error_message: Optional[str] = None
    
    documents: List[DocumentResponse] = []
    changes: List[ChangeResponse] = []

    class Config:
        from_attributes = True


class ReportResponse(BaseModel):
    """Ссылки на сгенерированные отчёты."""
    
    case_id: UUID
    html_url: Optional[str] = None
    pdf_url: Optional[str] = None
    json_url: Optional[str] = None


class CompareRequest(BaseModel):
    """Запрос на сравнение документов."""
    
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)


class ComparisonSummary(BaseModel):
    """Краткая сводка по сравнению."""
    
    total_changes: int
    semantic_changes: int
    technical_changes: int
    categories: Dict[ChangeCategory, int]
    impacts: Dict[ImpactLevel, int]
    overall_summary: str


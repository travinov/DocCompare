"""Модели для хранения результатов сравнения документов."""

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import JSON, Column, DateTime, Enum, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


class ComparisonCase(Base):
    """Кейс сравнения двух документов."""

    __tablename__ = "comparison_cases"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Статус обработки
    status = Column(
        Enum(
            "pending",      # Ожидает обработки
            "extracting",   # Извлечение текста
            "diffing",      # Diff-анализ
            "analyzing",    # LLM-анализ
            "generating",   # Генерация отчёта
            "completed",    # Завершено
            "failed",       # Ошибка
            name="case_status"
        ),
        default="pending",
        nullable=False
    )
    
    # Метаданные
    metadata_ = Column("metadata", JSON, default={})
    error_message = Column(Text, nullable=True)
    
    # Результаты анализа
    total_changes = Column(Integer, default=0)
    semantic_changes_count = Column(Integer, default=0)
    technical_changes_count = Column(Integer, default=0)
    
    # Оценка влияния
    overall_impact = Column(
        Enum("low", "medium", "high", name="impact_level"),
        nullable=True
    )
    
    # Сводка изменений
    summary = Column(Text, nullable=True)
    
    # Пути к отчётам
    html_report_path = Column(String, nullable=True)
    pdf_report_path = Column(String, nullable=True)
    json_report_path = Column(String, nullable=True)
    
    # Время обработки
    processing_time = Column(Float, nullable=True)  # секунды
    
    # Связи
    documents = relationship("ComparisonDocument", back_populates="case", cascade="all, delete-orphan")
    changes = relationship("ComparisonChange", back_populates="case", cascade="all, delete-orphan")


class ComparisonDocument(Base):
    """Документ в кейсе сравнения."""

    __tablename__ = "comparison_documents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    case_id = Column(UUID(as_uuid=True), ForeignKey("comparison_cases.id", ondelete="CASCADE"), nullable=False)
    
    # Тип документа (base или target)
    document_type = Column(
        Enum("base", "target", name="document_type"),
        nullable=False
    )
    
    # Информация о файле
    original_filename = Column(String, nullable=False)
    file_format = Column(String, nullable=False)  # doc, docx, pdf
    file_size = Column(Integer, nullable=False)  # bytes
    storage_path = Column(String, nullable=False)  # путь в S3/MinIO
    
    # Извлечённый текст
    extracted_text = Column(Text, nullable=True)
    normalized_text = Column(Text, nullable=True)
    
    # Структурированные данные
    structure = Column(JSON, nullable=True)  # разделы, абзацы и т.д.
    
    # OCR metadata (если использовался)
    is_scanned = Column(Integer, default=0)  # boolean as int
    ocr_confidence = Column(Float, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Связи
    case = relationship("ComparisonCase", back_populates="documents")


class ComparisonChange(Base):
    """Отдельное изменение, выявленное при сравнении."""

    __tablename__ = "comparison_changes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    case_id = Column(UUID(as_uuid=True), ForeignKey("comparison_cases.id", ondelete="CASCADE"), nullable=False)
    
    # Позиция в документе
    section = Column(String, nullable=True)  # раздел документа
    position = Column(Integer, nullable=False)  # порядковый номер изменения
    
    # Тип изменения (технический)
    change_type = Column(
        Enum("added", "removed", "modified", name="change_type"),
        nullable=False
    )
    
    # Текст изменений
    old_text = Column(Text, nullable=True)
    new_text = Column(Text, nullable=True)
    context_before = Column(Text, nullable=True)
    context_after = Column(Text, nullable=True)
    
    # Семантический анализ (от LLM)
    is_semantic_change = Column(Integer, default=0)  # boolean as int
    
    # Категория изменения
    category = Column(
        Enum(
            "dates",          # Сроки
            "obligations",    # Обязательства
            "financial",      # Финансовые параметры
            "conditions",     # Условия
            "parties",        # Стороны договора
            "technical",      # Технические детали
            "other",          # Прочее
            name="change_category"
        ),
        nullable=True
    )
    
    # Влияние изменения
    impact = Column(
        Enum("low", "medium", "high", name="impact_level"),
        nullable=True
    )
    
    # Описание от LLM
    llm_summary = Column(Text, nullable=True)
    llm_reasoning = Column(Text, nullable=True)
    
    # Эмбеддинги для семантического поиска (опционально)
    old_embedding = Column(JSON, nullable=True)
    new_embedding = Column(JSON, nullable=True)
    similarity_score = Column(Float, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Связи
    case = relationship("ComparisonCase", back_populates="changes")


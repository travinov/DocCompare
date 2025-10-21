"""Извлечение текста из различных форматов документов."""

import io
import re
from pathlib import Path
from typing import BinaryIO, Dict, List, Optional, Tuple

import fitz  # PyMuPDF
import pytesseract
from docx import Document
from pdf2image import convert_from_bytes
from PIL import Image

from app.core.config import settings
from app.core.logging_config import get_logger

logger = get_logger(__name__)


class TextExtractor:
    """Класс для извлечения текста из документов различных форматов."""

    def extract(
        self,
        file_data: BinaryIO,
        file_format: str,
        filename: str,
    ) -> Tuple[str, Dict, bool, Optional[float]]:
        """
        Извлекает текст из документа.
        
        Args:
            file_data: Файловые данные
            file_format: Формат файла (doc, docx, pdf)
            filename: Имя файла
            
        Returns:
            Кортеж: (извлечённый_текст, структура, is_scanned, ocr_confidence)
        """
        logger.info(f"Extracting text from {filename} ({file_format})")
        
        if file_format.lower() in ["doc", "docx"]:
            return self._extract_from_docx(file_data)
        elif file_format.lower() == "pdf":
            return self._extract_from_pdf(file_data)
        else:
            raise ValueError(f"Unsupported file format: {file_format}")

    def _extract_from_docx(
        self, file_data: BinaryIO
    ) -> Tuple[str, Dict, bool, Optional[float]]:
        """Извлекает текст из DOCX документа."""
        try:
            doc = Document(file_data)
            
            paragraphs = []
            structure = {"sections": []}
            
            current_section = {"title": "Main", "paragraphs": []}
            
            for para in doc.paragraphs:
                text = para.text.strip()
                if not text:
                    continue
                
                paragraphs.append(text)
                
                # Определяем заголовки (упрощённая логика)
                if para.style.name.startswith("Heading"):
                    if current_section["paragraphs"]:
                        structure["sections"].append(current_section)
                    current_section = {"title": text, "paragraphs": []}
                else:
                    current_section["paragraphs"].append(text)
            
            if current_section["paragraphs"]:
                structure["sections"].append(current_section)
            
            full_text = "\n\n".join(paragraphs)
            
            logger.info(f"Extracted {len(paragraphs)} paragraphs from DOCX")
            return full_text, structure, False, None
            
        except Exception as e:
            logger.error(f"Error extracting text from DOCX: {e}")
            raise

    def _extract_from_pdf(
        self, file_data: BinaryIO
    ) -> Tuple[str, Dict, bool, Optional[float]]:
        """Извлекает текст из PDF документа."""
        try:
            # Читаем байты
            pdf_bytes = file_data.read()
            file_data.seek(0)
            
            # Пробуем извлечь текстовый PDF
            doc = fitz.open(stream=pdf_bytes, filetype="pdf")
            
            text_pages = []
            structure = {"pages": []}
            
            has_text = False
            
            for page_num in range(len(doc)):
                page = doc[page_num]
                text = page.get_text()
                
                # Проверяем, есть ли текст на странице
                if text.strip():
                    has_text = True
                    text_pages.append(text)
                    structure["pages"].append({
                        "page_num": page_num + 1,
                        "text": text,
                    })
            
            doc.close()
            
            # Если текст найден - возвращаем
            if has_text:
                full_text = "\n\n".join(text_pages)
                logger.info(f"Extracted text from {len(text_pages)} PDF pages")
                return full_text, structure, False, None
            
            # Если текста нет - это скан, используем OCR
            logger.info("No text in PDF, using OCR")
            return self._extract_with_ocr(pdf_bytes)
            
        except Exception as e:
            logger.error(f"Error extracting text from PDF: {e}")
            raise

    def _extract_with_ocr(
        self, pdf_bytes: bytes
    ) -> Tuple[str, Dict, bool, float]:
        """Извлекает текст из сканированного PDF используя OCR."""
        try:
            # Конвертируем PDF в изображения
            images = convert_from_bytes(pdf_bytes)
            
            texts = []
            confidences = []
            structure = {"pages": []}
            
            for idx, image in enumerate(images):
                # Применяем OCR
                ocr_data = pytesseract.image_to_data(
                    image,
                    lang=settings.TESSERACT_LANG,
                    output_type=pytesseract.Output.DICT,
                )
                
                # Извлекаем текст
                page_text = pytesseract.image_to_string(
                    image,
                    lang=settings.TESSERACT_LANG,
                )
                
                texts.append(page_text)
                
                # Вычисляем среднюю уверенность OCR
                page_confidences = [
                    int(conf) for conf in ocr_data["conf"] if conf != "-1"
                ]
                if page_confidences:
                    avg_conf = sum(page_confidences) / len(page_confidences)
                    confidences.append(avg_conf)
                
                structure["pages"].append({
                    "page_num": idx + 1,
                    "text": page_text,
                    "ocr_confidence": avg_conf if page_confidences else 0,
                })
            
            full_text = "\n\n".join(texts)
            overall_confidence = sum(confidences) / len(confidences) if confidences else 0
            
            logger.info(
                f"OCR extracted text from {len(images)} pages, "
                f"avg confidence: {overall_confidence:.2f}%"
            )
            
            return full_text, structure, True, overall_confidence
            
        except Exception as e:
            logger.error(f"Error in OCR extraction: {e}")
            raise

    def normalize_text(self, text: str) -> str:
        """
        Нормализует текст: убирает лишние пробелы, унифицирует форматирование.
        
        Args:
            text: Исходный текст
            
        Returns:
            Нормализованный текст
        """
        # Убираем множественные пробелы
        text = re.sub(r"\s+", " ", text)
        
        # Убираем пробелы в начале и конце строк
        lines = [line.strip() for line in text.split("\n")]
        text = "\n".join(lines)
        
        # Убираем множественные переносы строк
        text = re.sub(r"\n{3,}", "\n\n", text)
        
        # Унифицируем кавычки
        text = text.replace("«", '"').replace("»", '"')
        text = text.replace(""", '"').replace(""", '"')
        
        # Унифицируем дефисы и тире
        text = text.replace("–", "-").replace("—", "-")
        
        # Убираем невидимые символы
        text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]", "", text)
        
        return text.strip()

    def segment_into_blocks(self, text: str) -> List[Dict[str, str]]:
        """
        Сегментирует текст на смысловые блоки (абзацы/предложения).
        
        Args:
            text: Текст для сегментации
            
        Returns:
            Список блоков с метаданными
        """
        blocks = []
        
        # Разбиваем на абзацы
        paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
        
        for idx, para in enumerate(paragraphs):
            # Разбиваем абзац на предложения
            sentences = self._split_sentences(para)
            
            blocks.append({
                "type": "paragraph",
                "index": idx,
                "text": para,
                "sentences": sentences,
                "sentence_count": len(sentences),
            })
        
        return blocks

    def _split_sentences(self, text: str) -> List[str]:
        """Разбивает текст на предложения."""
        # Простая логика разбиения по точкам, восклицательным и вопросительным знакам
        # Учитываем сокращения и числа
        pattern = r"(?<!\w\.\w.)(?<![A-ZА-Я][а-я]\.)(?<=\.|\?|\!)\s+"
        sentences = re.split(pattern, text)
        return [s.strip() for s in sentences if s.strip()]


"""Клиент для работы с S3/MinIO хранилищем."""

import io
from pathlib import Path
from typing import BinaryIO, Optional
from uuid import UUID

from minio import Minio
from minio.error import S3Error

from app.core.config import settings
from app.core.logging_config import get_logger

logger = get_logger(__name__)


class S3Storage:
    """Клиент для работы с S3-совместимым хранилищем."""

    def __init__(self):
        """Инициализация клиента MinIO."""
        self.client = Minio(
            settings.MINIO_ENDPOINT,
            access_key=settings.MINIO_ACCESS_KEY,
            secret_key=settings.MINIO_SECRET_KEY,
            secure=settings.MINIO_USE_SSL,
        )
        self.bucket_name = settings.MINIO_BUCKET_NAME
        self._ensure_bucket()

    def _ensure_bucket(self) -> None:
        """Создаёт bucket если его нет."""
        try:
            if not self.client.bucket_exists(self.bucket_name):
                self.client.make_bucket(self.bucket_name)
                logger.info(f"Created bucket: {self.bucket_name}")
        except S3Error as e:
            logger.error(f"Error creating bucket: {e}")
            raise

    def upload_file(
        self,
        file_data: BinaryIO,
        object_name: str,
        content_type: Optional[str] = None,
    ) -> str:
        """
        Загружает файл в хранилище.
        
        Args:
            file_data: Файловый объект для загрузки
            object_name: Имя объекта в хранилище
            content_type: MIME тип файла
            
        Returns:
            Путь к объекту в хранилище
        """
        try:
            # Получаем размер файла
            file_data.seek(0, 2)  # Перемещаемся в конец
            file_size = file_data.tell()
            file_data.seek(0)  # Возвращаемся в начало

            self.client.put_object(
                self.bucket_name,
                object_name,
                file_data,
                length=file_size,
                content_type=content_type or "application/octet-stream",
            )
            
            logger.info(f"Uploaded file: {object_name}")
            return f"{self.bucket_name}/{object_name}"
            
        except S3Error as e:
            logger.error(f"Error uploading file {object_name}: {e}")
            raise

    def upload_document(
        self,
        case_id: UUID,
        document_type: str,
        file_data: BinaryIO,
        filename: str,
    ) -> str:
        """
        Загружает документ для кейса сравнения.
        
        Args:
            case_id: ID кейса сравнения
            document_type: Тип документа (base/target)
            file_data: Файловые данные
            filename: Имя файла
            
        Returns:
            Путь к документу в хранилище
        """
        # Формируем путь: cases/{case_id}/{document_type}/{filename}
        object_name = f"cases/{case_id}/{document_type}/{filename}"
        
        # Определяем content_type
        suffix = Path(filename).suffix.lower()
        content_type_map = {
            ".pdf": "application/pdf",
            ".doc": "application/msword",
            ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        }
        content_type = content_type_map.get(suffix, "application/octet-stream")
        
        return self.upload_file(file_data, object_name, content_type)

    def download_file(self, object_name: str) -> bytes:
        """
        Скачивает файл из хранилища.
        
        Args:
            object_name: Имя объекта в хранилище
            
        Returns:
            Содержимое файла в байтах
        """
        try:
            response = self.client.get_object(self.bucket_name, object_name)
            data = response.read()
            response.close()
            response.release_conn()
            return data
        except S3Error as e:
            logger.error(f"Error downloading file {object_name}: {e}")
            raise

    def get_file_stream(self, object_name: str) -> BinaryIO:
        """
        Получает поток для чтения файла.
        
        Args:
            object_name: Имя объекта в хранилище
            
        Returns:
            Файловый поток
        """
        try:
            response = self.client.get_object(self.bucket_name, object_name)
            return io.BytesIO(response.read())
        except S3Error as e:
            logger.error(f"Error getting file stream {object_name}: {e}")
            raise

    def upload_report(
        self,
        case_id: UUID,
        report_type: str,
        content: bytes,
    ) -> str:
        """
        Загружает отчёт в хранилище.
        
        Args:
            case_id: ID кейса
            report_type: Тип отчёта (html/pdf/json)
            content: Содержимое отчёта
            
        Returns:
            Путь к отчёту
        """
        object_name = f"reports/{case_id}/report.{report_type}"
        
        content_type_map = {
            "html": "text/html",
            "pdf": "application/pdf",
            "json": "application/json",
        }
        
        return self.upload_file(
            io.BytesIO(content),
            object_name,
            content_type_map.get(report_type)
        )

    def get_presigned_url(self, object_name: str, expires_seconds: int = 3600) -> str:
        """
        Генерирует подписанный URL для доступа к файлу.
        
        Args:
            object_name: Имя объекта
            expires_seconds: Время жизни URL в секундах
            
        Returns:
            Подписанный URL
        """
        try:
            from datetime import timedelta
            url = self.client.presigned_get_object(
                self.bucket_name,
                object_name,
                expires=timedelta(seconds=expires_seconds),
            )
            return url
        except S3Error as e:
            logger.error(f"Error generating presigned URL for {object_name}: {e}")
            raise

    def delete_file(self, object_name: str) -> None:
        """Удаляет файл из хранилища."""
        try:
            self.client.remove_object(self.bucket_name, object_name)
            logger.info(f"Deleted file: {object_name}")
        except S3Error as e:
            logger.error(f"Error deleting file {object_name}: {e}")
            raise

    def delete_case_files(self, case_id: UUID) -> None:
        """Удаляет все файлы кейса."""
        prefix = f"cases/{case_id}/"
        try:
            objects = self.client.list_objects(self.bucket_name, prefix=prefix, recursive=True)
            for obj in objects:
                self.client.remove_object(self.bucket_name, obj.object_name)
            logger.info(f"Deleted all files for case: {case_id}")
        except S3Error as e:
            logger.error(f"Error deleting case files {case_id}: {e}")
            raise


# Singleton instance
_storage_instance: Optional[S3Storage] = None


def get_storage() -> S3Storage:
    """Получить экземпляр хранилища (singleton)."""
    global _storage_instance
    if _storage_instance is None:
        _storage_instance = S3Storage()
    return _storage_instance


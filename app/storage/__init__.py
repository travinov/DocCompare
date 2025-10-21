"""Модуль работы с файловым хранилищем."""

from .s3_client import S3Storage, get_storage

__all__ = ["S3Storage", "get_storage"]


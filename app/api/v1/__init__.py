"""API v1."""

from fastapi import APIRouter

from .endpoints import comparison, detailed_diff

api_router = APIRouter()

api_router.include_router(
    comparison.router,
    prefix="/compare",
    tags=["comparison"],
)

# Добавляем детальный diff как sub-router
comparison.router.include_router(
    detailed_diff.router,
    tags=["detailed-diff"],
)


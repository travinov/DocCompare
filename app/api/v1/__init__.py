"""API v1."""

from fastapi import APIRouter

from .endpoints import comparison

api_router = APIRouter()

api_router.include_router(
    comparison.router,
    prefix="/compare",
    tags=["comparison"],
)


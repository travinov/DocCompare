"""Тесты API endpoints."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_root(client: AsyncClient):
    """Тест корневого эндпоинта."""
    response = await client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "DocCompare"
    assert data["status"] == "running"


@pytest.mark.asyncio
async def test_health_check(client: AsyncClient):
    """Тест health check."""
    response = await client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


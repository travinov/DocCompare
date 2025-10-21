"""Главный файл FastAPI приложения."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from prometheus_client import make_asgi_app

from app.api.v1 import api_router
from app.core.config import settings
from app.core.database import init_db
from app.core.logging_config import get_logger, setup_logging

# Настраиваем логирование
setup_logging()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Жизненный цикл приложения."""
    # Startup
    logger.info("Starting DocCompare application...")
    
    # Инициализируем БД
    try:
        await init_db()
        logger.info("Database initialized")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
    
    yield
    
    # Shutdown
    logger.info("Shutting down DocCompare application...")


# Создаём приложение
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Система сравнения документов с семантическим анализом",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # В продакшене ограничить
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Подключаем API роутер
app.include_router(api_router, prefix=settings.API_V1_PREFIX)

# Prometheus metrics
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)


@app.get("/")
async def root():
    """Корневой эндпоинт."""
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running",
    }


@app.get("/health")
async def health_check():
    """Health check эндпоинт."""
    return {"status": "healthy"}


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Глобальный обработчик исключений."""
    import traceback
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    # В режиме DEBUG показываем детали ошибки
    if settings.DEBUG:
        return JSONResponse(
            status_code=500,
            content={
                "detail": "Internal server error",
                "error": str(exc),
                "traceback": traceback.format_exc(),
            },
        )
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
    )


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower(),
    )


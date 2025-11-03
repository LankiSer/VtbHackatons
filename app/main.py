"""
Главный файл приложения
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from contextlib import asynccontextmanager
from app.core.config import settings
from app.core.database import init_db, engine
from app.api import auth, banks

import os


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Инициализация при старте и очистка при остановке"""
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        logger.info("Starting application initialization...")
        # Инициализация БД
        await init_db()
        logger.info("Application initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize application: {e}")
        # Не падаем сразу, возможно БД просто еще не готова
        # При следующем запросе будет повторная попытка
        pass
    
    yield
    
    # Очистка при остановке
    logger.info("Shutting down application...")
    await engine.dispose()
    logger.info("Application shut down")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Мультибанковское финансовое приложение",
    lifespan=lifespan
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Подключение роутеров
app.include_router(auth.router)
app.include_router(banks.router)

# Статические файлы для фронтенда
frontend_path = os.path.join(os.path.dirname(__file__), "..", "frontend")
if os.path.exists(frontend_path):
    app.mount("/static", StaticFiles(directory=frontend_path), name="static")


@app.get("/", response_class=HTMLResponse)
async def root():
    """Главная страница"""
    html_path = os.path.join(os.path.dirname(__file__), "..", "frontend", "index.html")
    if os.path.exists(html_path):
        with open(html_path, "r", encoding="utf-8") as f:
            return f.read()
    return """
    <html>
        <head><title>Мультибанк</title></head>
        <body>
            <h1>Мультибанковское приложение</h1>
            <p>API работает! Откройте <a href="/static/index.html">фронтенд</a></p>
            <p><a href="/docs">API документация</a></p>
        </body>
    </html>
    """


@app.get("/health")
async def health():
    """Health check endpoint"""
    return {"status": "ok", "version": settings.APP_VERSION}


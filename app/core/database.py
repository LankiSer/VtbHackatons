"""
Подключение к базе данных
"""
import logging
import asyncio
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base
from sqlalchemy.exc import OperationalError
from sqlalchemy import text
from app.core.config import settings

logger = logging.getLogger(__name__)

# Логируем DATABASE_URL для отладки (без пароля)
db_url_for_log = settings.DATABASE_URL.split('@')[1] if '@' in settings.DATABASE_URL else 'hidden'
logger.info(f"Connecting to database at: {db_url_for_log}")

engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    future=True,
    pool_pre_ping=True,  # Проверка соединения перед использованием
    pool_recycle=3600,  # Переподключение каждый час
)

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)

Base = declarative_base()


async def get_db() -> AsyncSession:
    """Dependency для получения сессии БД"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


async def check_db_connection(retries: int = 5, delay: float = 2.0):
    """Проверка подключения к БД с повторными попытками"""
    for attempt in range(retries):
        try:
            async with engine.begin() as conn:
                await conn.execute(text("SELECT 1"))
            logger.info("Database connection successful")
            return True
        except Exception as e:
            logger.warning(f"Database connection attempt {attempt + 1}/{retries} failed: {e}")
            if attempt < retries - 1:
                await asyncio.sleep(delay)
            else:
                logger.error(f"Failed to connect to database after {retries} attempts")
                raise
    return False


async def init_db():
    """Инициализация БД: создание таблиц"""
    try:
        # Проверяем подключение перед созданием таблиц
        await check_db_connection()
        
        logger.info("Creating database tables...")
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        # Логируем полный DATABASE_URL для отладки (в проде нужно убрать)
        if settings.DEBUG:
            logger.error(f"Database URL: {settings.DATABASE_URL}")
        raise


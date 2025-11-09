"""
Конфигурация приложения
"""
from pydantic_settings import BaseSettings
from typing import List, Dict


class Settings(BaseSettings):
    """Настройки мультибанковского приложения"""
    
    # === ПРИЛОЖЕНИЕ ===
    APP_NAME: str = "Мультибанк"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    
    # === DATABASE ===
    # По умолчанию для Docker (используется db как hostname)
    # Для локальной разработки можно переопределить через .env или переменные окружения
    DATABASE_URL: str = "postgresql+asyncpg://multibank_user:multibank_pass@db:5432/multibank_db"
    
    # === SECURITY ===
    SECRET_KEY: str = "your-secret-key-change-in-production-use-env-var"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 24 hours
    
    # === БАНКИ (из песочницы) ===
    # Можно использовать локальные банки из Docker или внешние URL
    # Для локальных банков используйте USE_LOCAL_BANKS=true в .env
    USE_LOCAL_BANKS: bool = False  # По умолчанию используем локальные банки из Docker
    
    # URL банков - автоматически выбираются на основе USE_LOCAL_BANKS
    # Локальные банки из Docker (запущенные через docker-compose)
    LOCAL_BANKS: Dict[str, Dict[str, str]] = {
        "vbank": {
            "name": "Virtual Bank",
            "base_url": "http://vbank:8001",
            "auth_url": "http://vbank:8001/auth/bank-token",
            "well_known_url": "http://vbank:8001/.well-known/jwks.json",
            "client_id": "team227", 
            "client_secret": "RKlNZd4YRCracyqH8I2LsdXHU2aq3yw9"
        },
        "abank": {
            "name": "A Bank",
            "base_url": "http://abank:8002",
            "auth_url": "http://abank:8002/auth/bank-token",
            "well_known_url": "http://abank:8002/.well-known/jwks.json",
            "client_id": "team227",
            "client_secret": "RKlNZd4YRCracyqH8I2LsdXHU2aq3yw9"
        },
        "sbank": {
            "name": "S Bank",
            "base_url": "http://sbank:8003",
            "auth_url": "http://sbank:8003/auth/bank-token",
            "well_known_url": "http://sbank:8003/.well-known/jwks.json",
            "client_id": "team227",
            "client_secret": "RKlNZd4YRCracyqH8I2LsdXHU2aq3yw9"
        }
    }
    
    # Внешние банки из песочницы
    EXTERNAL_BANKS: Dict[str, Dict[str, str]] = {
        "vbank": {
            "name": "Virtual Bank",
            "base_url": "https://vbank.open.bankingapi.ru",
            "auth_url": "https://vbank.open.bankingapi.ru/auth/bank-token",
            "well_known_url": "https://vbank.open.bankingapi.ru/.well-known/jwks.json",
            "client_id": "team227",
            "client_secret": "RKlNZd4YRCracyqH8I2LsdXHU2aq3yw9"
        },
        "abank": {
            "name": "A Bank",
            "base_url": "https://abank.open.bankingapi.ru",
            "auth_url": "https://abank.open.bankingapi.ru/auth/bank-token",
            "well_known_url": "https://abank.open.bankingapi.ru/.well-known/jwks.json",
            "client_id": "team227",
            "client_secret": "RKlNZd4YRCracyqH8I2LsdXHU2aq3yw9"
        },
        "sbank": {
            "name": "S Bank",
            "base_url": "https://sbank.open.bankingapi.ru",
            "auth_url": "https://sbank.open.bankingapi.ru/auth/bank-token",
            "well_known_url": "https://sbank.open.bankingapi.ru/.well-known/jwks.json",
            "client_id": "team227",
            "client_secret": "RKlNZd4YRCracyqH8I2LsdXHU2aq3yw9"
        }
    }
    
    def get_banks(self) -> Dict[str, Dict[str, str]]:
        """Получить конфигурацию банков в зависимости от режима"""
        return self.LOCAL_BANKS if self.USE_LOCAL_BANKS else self.EXTERNAL_BANKS
    
    # === CORS ===
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:8080",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:8080",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
        "http://0.0.0.0:8000",
    ]
    CORS_ORIGIN_REGEX: str | None = r"http://(localhost|127\.0\.0\.1|0\.0\.0\.0)(:\d+)?"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()


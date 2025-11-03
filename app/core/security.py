"""
Безопасность: хеширование паролей, создание JWT токенов
"""
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from jose import JWTError, jwt
from passlib.context import CryptContext
from app.core.config import settings

pwd_context = CryptContext(
    schemes=["argon2", "bcrypt"],  # argon2 — по умолчанию для новых хэшей, bcrypt — для совместимости
    deprecated="auto",
)


def _truncate_for_bcrypt(input_text: str) -> str:
    """Truncate input to 72 bytes for bcrypt compatibility (UTF-8 safe)."""
    if input_text is None:
        return ""
    raw = input_text.encode("utf-8")
    if len(raw) <= 72:
        return input_text
    # Truncate to 72 bytes and decode ignoring incomplete multibyte tails
    return raw[:72].decode("utf-8", errors="ignore")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Проверка пароля"""
    # bcrypt ограничивает длину входа 72 байт
    safe_plain = _truncate_for_bcrypt(plain_password)
    return pwd_context.verify(safe_plain, hashed_password)


def get_password_hash(password: str) -> str:
    """Хеширование пароля"""
    # bcrypt ограничивает длину входа 72 байт
    safe_password = _truncate_for_bcrypt(password)
    return pwd_context.hash(safe_password)


def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """Создание JWT токена"""
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    # JWT spec: sub SHOULD be a string. Приводим к строке при наличии.
    if "sub" in to_encode and to_encode["sub"] is not None:
        to_encode["sub"] = str(to_encode["sub"]) 
    to_encode.update({"exp": expire, "iat": datetime.utcnow()})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def decode_access_token(token: str) -> Optional[Dict[str, Any]]:
    """Декодирование JWT токена"""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except JWTError:
        return None


def encrypt_token(token: str) -> str:
    """Шифрование токена для хранения в БД (базовая реализация)"""
    # В production используйте более надежное шифрование
    # Например, через cryptography.fernet
    return token


def decrypt_token(encrypted_token: str) -> str:
    """Расшифровка токена из БД"""
    return encrypted_token


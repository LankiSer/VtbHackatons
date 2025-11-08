"""
Модели подключений к банкам
"""
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import Base


class BankConnection(Base):
    """Подключение пользователя к банку"""
    __tablename__ = "bank_connections"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    bank_code = Column(String(50), nullable=False, index=True)  # vbank, abank, sbank
    bank_name = Column(String(255))
    team_client_id = Column(String(100), nullable=True)  # team227-1
    team_client_secret = Column(Text, nullable=True)  # хранится для обновления токена
    
    # OAuth токены (зашифрованные)
    access_token = Column(Text, nullable=False)  # Зашифрованный токен
    refresh_token = Column(Text, nullable=True)  # Если поддерживается
    token_expires_at = Column(DateTime, nullable=True)
    
    # Согласие (consent)
    consent_id = Column(String(100), nullable=True)
    consent_status = Column(String(50), default="pending")  # pending, authorized, revoked
    
    # Статус подключения
    is_active = Column(Boolean, default=True)
    last_sync_at = Column(DateTime, nullable=True)
    connected_at = Column(DateTime, default=datetime.utcnow)
    revoked_at = Column(DateTime, nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="bank_connections")


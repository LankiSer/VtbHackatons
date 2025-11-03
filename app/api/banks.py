"""
API для работы с банками
"""
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime
from app.core.database import get_db
from app.core.config import settings
from app.models.user import User
from app.models.bank_connection import BankConnection
from app.api.dependencies import get_current_user
from app.services.bank_service import BankService

router = APIRouter(prefix="/api/banks", tags=["Banks"])


class BankInfo(BaseModel):
    """Информация о банке"""
    code: str
    name: str
    base_url: str


class BankConnectionResponse(BaseModel):
    """Ответ с подключением к банку"""
    id: int
    bank_code: str
    bank_name: str
    is_active: bool
    connected_at: str
    last_sync_at: Optional[str]
    
    class Config:
        from_attributes = True


class ConnectBankRequest(BaseModel):
    """Запрос на подключение банка"""
    bank_code: str
    client_id: str
    client_secret: str


@router.get("/available", response_model=List[BankInfo])
async def get_available_banks():
    """Получить список доступных банков"""
    banks = settings.get_banks()
    return [
        BankInfo(
            code=code,
            name=config["name"],
            base_url=config["base_url"]
        )
        for code, config in banks.items()
    ]


@router.get("/connections", response_model=List[BankConnectionResponse])
async def get_my_connections(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Получить подключения пользователя к банкам"""
    result = await db.execute(
        select(BankConnection).where(BankConnection.user_id == current_user.id)
    )
    connections = result.scalars().all()
    
    return [
        BankConnectionResponse(
            id=conn.id,
            bank_code=conn.bank_code,
            bank_name=conn.bank_name,
            is_active=conn.is_active,
            connected_at=conn.connected_at.isoformat(),
            last_sync_at=conn.last_sync_at.isoformat() if conn.last_sync_at else None
        )
        for conn in connections
    ]


@router.post("/connect", response_model=BankConnectionResponse, status_code=status.HTTP_201_CREATED)
async def connect_bank(
    request: ConnectBankRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Начать процесс подключения банка"""
    banks = settings.get_banks()
    # Проверить, существует ли банк
    if request.bank_code not in banks:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Bank '{request.bank_code}' not found"
        )
    
    # Проверить, не подключен ли уже этот банк
    result = await db.execute(
        select(BankConnection).where(
            BankConnection.user_id == current_user.id,
            BankConnection.bank_code == request.bank_code,
            BankConnection.is_active == True
        )
    )
    existing = result.scalar_one_or_none()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Bank '{request.bank_code}' is already connected"
        )
    
    # Получить токен от банка через сервис используя учетные данные пользователя
    banks = settings.get_banks()
    bank_config = banks[request.bank_code]
    
    # Используем учетные данные от пользователя
    user_bank_config = bank_config.copy()
    user_bank_config["client_id"] = request.client_id
    user_bank_config["client_secret"] = request.client_secret
    
    bank_service = BankService(user_bank_config)
    
    try:
        token_data = await bank_service.get_bank_token()
        access_token = token_data["access_token"]
        
        # Создать подключение
        connection = BankConnection(
            user_id=current_user.id,
            bank_code=request.bank_code,
            bank_name=bank_config["name"],
            access_token=access_token,  # В production здесь должно быть шифрование
            token_expires_at=datetime.utcnow().replace(hour=23, minute=59, second=59)  # Примерно 24 часа
        )
        
        db.add(connection)
        await db.commit()
        await db.refresh(connection)
        
        return BankConnectionResponse(
            id=connection.id,
            bank_code=connection.bank_code,
            bank_name=connection.bank_name,
            is_active=connection.is_active,
            connected_at=connection.connected_at.isoformat(),
            last_sync_at=None
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to connect to bank: {str(e)}"
        )


@router.delete("/connections/{bank_code}", status_code=status.HTTP_204_NO_CONTENT)
async def disconnect_bank(
    bank_code: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Отключить банк"""
    result = await db.execute(
        select(BankConnection).where(
            BankConnection.user_id == current_user.id,
            BankConnection.bank_code == bank_code,
            BankConnection.is_active == True
        )
    )
    connection = result.scalar_one_or_none()
    
    if not connection:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bank connection not found"
        )
    
    connection.is_active = False
    connection.revoked_at = datetime.utcnow()
    
    await db.commit()


"""
API для работы с банками
"""
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
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


async def _get_active_connection(
    db: AsyncSession,
    user_id: int,
    bank_code: str
) -> BankConnection | None:
    result = await db.execute(
        select(BankConnection).where(
            BankConnection.user_id == user_id,
            BankConnection.bank_code == bank_code,
            BankConnection.is_active == True
        )
    )
    return result.scalar_one_or_none()


def _build_bank_service(bank_code: str, connection: BankConnection | None = None) -> BankService:
    banks = settings.get_banks()
    if bank_code not in banks:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Bank '{bank_code}' not found"
        )
    
    bank_config = banks[bank_code].copy()
    if connection:
        if connection.team_client_id:
            bank_config["client_id"] = connection.team_client_id
        if connection.team_client_secret:
            bank_config["client_secret"] = connection.team_client_secret
    
    return BankService(bank_config)


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
    consent_status: Optional[str] = None
    consent_id: Optional[str] = None
    
    class Config:
        from_attributes = True


class ConnectBankRequest(BaseModel):
    """Запрос на подключение банка"""
    bank_code: str
    client_id: str
    client_secret: str


class ConsentCreateRequest(BaseModel):
    """Запрос на создание согласия в банке"""
    client_id: str
    permissions: List[str] = [
        "ReadAccountsDetail",
        "ReadBalances",
        "ReadTransactionsDetail"
    ]
    requesting_bank_name: Optional[str] = None


class ConsentStatusResponse(BaseModel):
    """Ответ о статусе согласия"""
    consent_id: Optional[str] = None
    request_id: Optional[str] = None
    status: str
    message: Optional[str] = None
    auto_approved: Optional[bool] = None


class BankClientsResponse(BaseModel):
    """Ответ со списком клиентов банка"""
    clients: List[Dict[str, Any]]


class AccountsResponse(BaseModel):
    """Ответ со списком счетов"""
    data: Dict[str, Any]


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
            last_sync_at=conn.last_sync_at.isoformat() if conn.last_sync_at else None,
            consent_status=conn.consent_status,
            consent_id=conn.consent_id
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
            team_client_id=request.client_id,
            team_client_secret=request.client_secret,
            access_token=access_token,
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
            last_sync_at=None,
            consent_status=connection.consent_status,
            consent_id=connection.consent_id
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


@router.get(
    "/connections/{bank_code}/clients",
    response_model=BankClientsResponse,
    summary="Получить список клиентов банка"
)
async def get_bank_clients(
    bank_code: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Получить список доступных клиентов банка (для выбора person_id)."""
    connection = await _get_active_connection(db, current_user.id, bank_code)
    if not connection:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Bank '{bank_code}' is not connected"
        )

    bank_service = _build_bank_service(bank_code, connection)

    try:
        response = await bank_service.get_clients(
            access_token=connection.access_token,
            requesting_bank=connection.team_client_id
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Failed to fetch clients: {str(e)}"
        )

    if isinstance(response, list):
        clients = response
    elif isinstance(response, dict):
        clients = response.get("clients")
        if clients is None:
            data_block = response.get("data")
            if isinstance(data_block, list):
                clients = data_block
            elif isinstance(data_block, dict):
                clients = data_block.get("clients")
        if clients is None:
            clients = []
    else:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Unexpected clients payload type: {type(response).__name__}"
        )
    return BankClientsResponse(clients=clients)


@router.post(
    "/connections/{bank_code}/consents",
    response_model=ConsentStatusResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Создать согласие на доступ к данным"
)
async def create_bank_consent(
    bank_code: str,
    request: ConsentCreateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Запросить согласие у банка для доступа к данным клиента."""
    connection = await _get_active_connection(db, current_user.id, bank_code)
    if not connection:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Bank '{bank_code}' is not connected"
        )

    bank_service = _build_bank_service(bank_code, connection)

    try:
        result = await bank_service.create_consent(
            access_token=connection.access_token,
            permissions=request.permissions,
            client_id=request.client_id,
            requesting_bank=connection.team_client_id,
            requesting_bank_name=request.requesting_bank_name or "Мультибанк"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Failed to create consent: {str(e)}"
        )

    connection.consent_status = result.get("status", connection.consent_status)
    new_consent_id = result.get("consent_id") or result.get("request_id")
    if new_consent_id:
        connection.consent_id = new_consent_id
    connection.last_sync_at = datetime.utcnow()
    await db.commit()
    await db.refresh(connection)

    return ConsentStatusResponse(
        consent_id=result.get("consent_id"),
        request_id=result.get("request_id"),
        status=result.get("status", "pending"),
        message=result.get("message"),
        auto_approved=result.get("auto_approved")
    )


@router.get(
    "/connections/{bank_code}/accounts",
    response_model=AccountsResponse,
    summary="Получить счета из подключённого банка"
)
async def get_bank_accounts(
    bank_code: str,
    client_id: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Получить список счетов клиента из подключённого банка."""
    connection = await _get_active_connection(db, current_user.id, bank_code)
    if not connection:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Bank '{bank_code}' is not connected"
        )

    if not client_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="client_id is required to fetch accounts"
        )

    bank_service = _build_bank_service(bank_code, connection)

    try:
        accounts = await bank_service.get_accounts(
            access_token=connection.access_token,
            requesting_bank=connection.team_client_id,
            client_id=client_id,
            consent_id=connection.consent_id
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Failed to fetch accounts: {str(e)}"
        )

    connection.last_sync_at = datetime.utcnow()
    await db.commit()

    return AccountsResponse(data=accounts)


@router.get(
    "/connections/{bank_code}/transactions",
    response_model=AccountsResponse,
    summary="Получить транзакции из подключённого банка"
)
async def get_bank_transactions(
    bank_code: str,
    account_id: Optional[str] = None,
    client_id: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Получить транзакции клиента (по счету или все)."""
    connection = await _get_active_connection(db, current_user.id, bank_code)
    if not connection:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Bank '{bank_code}' is not connected"
        )

    if not account_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="account_id is required to fetch transactions"
        )

    if not client_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="client_id is required to fetch transactions"
        )

    bank_service = _build_bank_service(bank_code, connection)

    try:
        transactions = await bank_service.get_transactions(
            access_token=connection.access_token,
            account_id=account_id,
            requesting_bank=connection.team_client_id,
            client_id=client_id,
            consent_id=connection.consent_id
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Failed to fetch transactions: {str(e)}"
        )

    connection.last_sync_at = datetime.utcnow()
    await db.commit()

    return AccountsResponse(data=transactions)

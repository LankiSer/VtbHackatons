"""
Сервис для работы с банковскими API
"""
import httpx
from typing import Dict, Any


class BankService:
    """Сервис для взаимодействия с банковским API"""
    
    def __init__(self, bank_config: Dict[str, str]):
        self.config = bank_config
        self.base_url = bank_config["base_url"]
        self.client_id = bank_config.get("client_id")
        self.client_secret = bank_config.get("client_secret")
    
    async def get_bank_token(self) -> Dict[str, Any]:
        """Получить токен от банка"""
        if not self.client_id or not self.client_secret:
            raise Exception("Bank credentials are not configured")

        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.config["auth_url"],
                params={
                    "client_id": self.client_id,
                    "client_secret": self.client_secret
                },
                timeout=30.0
            )
            
            if response.status_code != 200:
                raise Exception(f"Failed to get token: {response.status_code} - {response.text}")
            
            return response.json()
    
    async def get_accounts(
        self,
        access_token: str,
        requesting_bank: str | None = None
    ) -> Dict[str, Any]:
        """Получить счета клиента"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/accounts",
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "X-Requesting-Bank": requesting_bank or self.client_id or ""
                },
                timeout=30.0
            )
            
            if response.status_code != 200:
                raise Exception(f"Failed to get accounts: {response.status_code} - {response.text}")
            
            return response.json()
    
    async def get_transactions(
        self,
        access_token: str,
        account_id: str | None = None,
        requesting_bank: str | None = None
    ) -> Dict[str, Any]:
        """Получить транзакции"""
        url = f"{self.base_url}/transactions"
        if account_id:
            url += f"?account_id={account_id}"
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                url,
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "X-Requesting-Bank": requesting_bank or self.client_id or ""
                },
                timeout=30.0
            )
            
            if response.status_code != 200:
                raise Exception(f"Failed to get transactions: {response.status_code} - {response.text}")
            
            return response.json()
    
    async def create_consent(
        self,
        access_token: str,
        permissions: list,
        client_id: str,
        requesting_bank: str | None = None,
        requesting_bank_name: str | None = None
    ) -> Dict[str, Any]:
        """Создать согласие для доступа к данным"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/account-consents/request",
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "X-Requesting-Bank": requesting_bank or self.client_id or "",
                    "Content-Type": "application/json"
                },
                json={
                    "client_id": client_id,
                    "permissions": permissions,
                    "reason": "Мультибанковское приложение",
                    "requesting_bank": requesting_bank or self.client_id,
                    "requesting_bank_name": requesting_bank_name or "Мультибанк"
                },
                timeout=30.0
            )
            
            if response.status_code not in [200, 201]:
                raise Exception(f"Failed to create consent: {response.status_code} - {response.text}")
            
            return response.json()

    async def get_clients(self) -> Dict[str, Any]:
        """Получить список клиентов банка (banker API)"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/banker/clients",
                timeout=30.0
            )

            if response.status_code != 200:
                raise Exception(f"Failed to get clients: {response.status_code} - {response.text}")

            return response.json()


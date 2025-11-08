
docker cp add-bank-connection-team-columns.sql multibank-db:/app/
docker exec -i multibank-db psql -U multibank_user -d multibank_db -f /app/add-bank-connection-team-columns.sql



docker exec -i vbank-db psql -U hackapi_user -d vbank_db < bank-in-a-box/shared/database/add-teams.sql
docker exec -i abank-db psql -U hackapi_user -d abank_db < bank-in-a-box/shared/database/add-teams.sql
docker exec -i sbank-db psql -U hackapi_user -d sbank_db < bank-in-a-box/shared/database/add-teams.sql

docker exec vbank-db psql -U hackapi_user -d vbank_db -c "SELECT client_id, team_name FROM teams;"
docker exec abank-db psql -U hackapi_user -d abank_db -c "SELECT client_id, team_name FROM teams;"
docker exec sbank-db psql -U hackapi_user -d sbank_db -c "SELECT client_id, team_name FROM teams;"


curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
        "username": "user@example.com",
        "password": "user-password"
      }'


Authorization: Bearer <access_token>

Подключение банка

curl -X POST http://localhost:8000/api/banks/connect \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{
        "bank_code": "vbank",
        "client_id": "team200",
        "client_secret": "5OAaa4DYzYKfnOU6zbR34ic5qMm7VSMB"
      }'

Ответ содержит `id` подключения и базовую информацию о банке.

Список подключений:

curl -X GET http://localhost:8000/api/banks/connections \
  -H "Authorization: Bearer <access_token>"

Получение списка клиентов банка


curl -X GET http://localhost:8000/api/banks/connections/vbank/clients \
  -H "Authorization: Bearer <access_token>"


Ответ включает массив `clients`; поле `person_id` требуется на следующем шаге.

Запрос согласия на доступ к данным


curl -X POST http://localhost:8000/api/banks/connections/vbank/consents \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{
        "client_id": "cli-vb-001",
        "permissions": [
          "ReadAccountsDetail",
          "ReadBalances",
          "ReadTransactionsDetail"
        ],
        "requesting_bank_name": "Multibank App"
      }'


В ответе возвращаются `status`, `request_id` и (при автоодобрении) `consent_id`.

curl -X GET http://localhost:8000/api/banks/connections/vbank/accounts \
  -H "Authorization: Bearer <access_token>"

Ответ содержит `data` из банка, включая `accountNumber`, `balance`, `currency`.

Получение транзакций

Все транзакции клиента:


curl -X GET "http://localhost:8000/api/banks/connections/vbank/transactions" \
  -H "Authorization: Bearer <access_token>"


Транзакции по конкретному счёту:


curl -X GET "http://localhost:8000/api/banks/connections/vbank/transactions?account_id=40817810099910001001" \
  -H "Authorization: Bearer <access_token>"


Отключение банка


curl -X DELETE http://localhost:8000/api/banks/connections/vbank \
  -H "Authorization: Bearer <access_token>"


Подключение переводится в статус `inactive`, токен и согласие перестают использоваться.


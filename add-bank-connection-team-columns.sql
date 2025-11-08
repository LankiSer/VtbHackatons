-- Добавляет служебные поля для хранения team credentials в таблице bank_connections
-- Запускать внутри контейнера multibank-db:
-- docker exec -i multibank-db psql -U multibank_user -d multibank_db -f /app/add-bank-connection-team-columns.sql

ALTER TABLE bank_connections
    ADD COLUMN IF NOT EXISTS team_client_id VARCHAR(100);

ALTER TABLE bank_connections
    ADD COLUMN IF NOT EXISTS team_client_secret TEXT;


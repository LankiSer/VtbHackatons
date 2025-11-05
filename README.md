# Мультибанковское приложение

Единый интерфейс для работы с несколькими банками через Open Banking API.

## Требования

- Docker и Docker Compose
- Git

## Установка

1. **Клонируйте репозиторий:**
```bash
git clone https://github.com/LankiSer/VtbHackatons.git
cd VtbHackatons
```

2. **Проверьте наличие всех файлов:**

Убедитесь, что директория `bank-in-a-box` содержит файл `Dockerfile`. Если его нет, проверьте, что все файлы были закоммичены:

```bash
ls -la bank-in-a-box/Dockerfile
```

Если файла нет, возможно нужно:
- Убедиться, что вы склонировали весь репозиторий
- Проверить, что в `.gitignore` не указана директория `bank-in-a-box`
- Если `bank-in-a-box` был добавлен как submodule, нужно его инициализировать:
```bash
git submodule update --init --recursive
```

3. **Запустите приложение:**

```bash
docker-compose up --build
```

## Структура проекта

```
VtbHackatons/
├── app/                    # Основное приложение (мультибанк)
│   ├── api/               # API endpoints
│   ├── core/              # Конфигурация и база данных
│   ├── models/            # Модели данных
│   └── services/          # Бизнес-логика
├── bank-in-a-box/         # Банки (vbank, abank, sbank)
│   ├── Dockerfile         # Dockerfile для банков
│   ├── api/               # API банков
│   └── shared/            # Общие ресурсы
├── frontend/               # Фронтенд
├── docker-compose.yml      # Конфигурация Docker
└── Dockerfile             # Dockerfile для основного приложения
```

## Использование

После запуска приложение будет доступно по адресам:

- **Мультибанк API:** http://localhost:8000
- **Фронтенд:** http://localhost:8000/static/index.html
- **VBank API:** http://localhost:8001
- **ABank API:** http://localhost:8002
- **SBank API:** http://localhost:8003

## Решение проблем

### Ошибка: "failed to read dockerfile: open Dockerfile: no such file or directory"

**Причина:** Dockerfile не найден в директории `bank-in-a-box`.

**Решение:**

1. Проверьте наличие файла:
```bash
ls bank-in-a-box/Dockerfile
```

2. Если файла нет, убедитесь что:
   - Вы склонировали весь репозиторий
   - Директория `bank-in-a-box` не пустая
   - В `.gitignore` не исключена директория `bank-in-a-box`

3. Если `bank-in-a-box` был добавлен как submodule:
```bash
git submodule update --init --recursive
```

4. Если ничего не помогает, скопируйте Dockerfile из другого места или создайте его заново на основе шаблона в репозитории.

### Ошибка: "version is obsolete"

Это предупреждение можно игнорировать. Версия `version: '3.8'` была удалена из `docker-compose.yml`, так как в новых версиях Docker Compose она не нужна.

## Переменные окружения

Создайте файл `.env` на основе `.env.example`:

```bash
cp .env.example .env
```

Отредактируйте `.env` и укажите необходимые параметры.

## Разработка

Для разработки с hot-reload:

```bash
docker-compose up
```

Изменения в коде будут автоматически подхватываться благодаря volume mounts.

## Лицензия

MIT


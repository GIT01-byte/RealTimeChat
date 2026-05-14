# 💬 RealTimeChat

Мессенджер реального времени на основе WebSockets с регистрацией/аутентификацией и обменом медиафайлами.

---

## 🏗️ Архитектура

Проект построен на микросервисной архитектуре:

```
Клиент (Vue 3)
    │
    ▼
Nginx (балансировщик, rate limiting)
    │
    ├── KrakenD (API Gateway)
    │       ├── Users-service  (FastAPI) — аутентификация, JWT
    │       ├── Chat-service   (FastAPI) — сообщения, WebSocket
    │       └── Media-service  (FastAPI) — загрузка файлов, S3, RabbitMQ
    │
    └── WebSocket (напрямую) → Chat-service
```

---

## 🛠️ Стек

| Слой | Технологии |
|---|---|
| Frontend | Vue 3 + Vite + Vue Router 4 |
| Backend | FastAPI + WebSockets + Dishka DI |
| API Gateway | KrakenD |
| БД | PostgreSQL + SQLAlchemy (async) + Alembic |
| Кэш | Redis |
| Очереди | RabbitMQ (Outbox pattern) |
| Хранилище | S3 (Selectel) |
| Антивирус | ClamAV |
| Балансировщик | Nginx |
| Контейнеризация | Docker + Docker Compose |

---

## ✅ Возможности

- **Микросервисная архитектура** — независимый деплой и масштабирование каждого сервиса
- **WebSocket** — мгновенная доставка сообщений без polling
- **JWT аутентификация** — EdDSA ключи, refresh токены, blacklist в Redis
- **Outbox pattern** — гарантированная доставка событий через RabbitMQ
- **Rate limiting** — защита от брутфорса и DDoS на уровне Nginx
- **Async I/O** — полностью асинхронный стек (asyncpg, aio-pika, httpx)
- **DI контейнер** — Dishka для управления зависимостями
- **Онлайн статусы** — отображение активных пользователей в реальном времени
- **Поиск пользователей** — поиск по имени с debounce
- **Медиафайлы** — загрузка изображений, видео, аудио через отдельный сервис
- **Антивирусная проверка** — сканирование загружаемых файлов через ClamAV
- **Адаптивный интерфейс** — поддержка мобильных устройств и планшетов

---

## 📁 Структура проекта

```
RealTimeChat/
├── Chat-service/       — сообщения, WebSocket, онлайн статусы
├── Users-service/      — регистрация, аутентификация, JWT
├── Media-service/      — загрузка файлов, S3, Outbox, ClamAV
├── frontend/           — Vue 3 SPA
├── nginx.conf.template — конфиг балансировщика
├── krakend.json        — конфиг API Gateway
├── docker-compose.yaml — основная конфигурация
└── .env.template       — шаблон переменных окружения
```

---

## 🚀 Деплой

### Требования
- Docker
- Git

### Установка

```bash
# 1. Клонировать репозиторий
git clone https://github.com/GIT01-byte/RealTimeChat.git
cd RealTimeChat

# 2. Настроить переменные окружения
cp .env.template .env
# Заполнить .env своими значениями

# 3. Добавить пользователя в группу docker (Linux)
sudo usermod -aG docker $USER
newgrp docker

# 4. Запустить
docker compose up --build
```

### Переменные окружения

| Переменная | Описание |
|---|---|
| `SERVER_NAME` | IP или домен сервера |
| `RTCHAT_APP_MODE` | Режим запуска Chat-service (`DEV` / `PROD`) |
| `RTCHAT_DB_*` | Настройки БД Chat-service |
| `RTCHAT_REDIS_*` | Настройки Redis Chat-service |
| `USERS_APP_MODE` | Режим запуска Users-service (`DEV` / `PROD`) |
| `USERS_DB_*` | Настройки БД Users-service |
| `USERS_REDIS_*` | Настройки Redis Users-service |
| `MEDIA_APP_MODE` | Режим запуска Media-service (`DEV` / `PROD`) |
| `MEDIA_DB_*` | Настройки БД Media-service |
| `MEDIA_S3_*` | Настройки S3 хранилища |
| `MEDIA_RABBITMQ_*` | Настройки RabbitMQ |
| `MEDIA_OUTBOX_ENABLED` | Включить Outbox воркеры (`True` / `False`) |
| `MEDIA_OUTBOX_POLL_INTERVAL` | Интервал опроса Outbox в секундах |

---

## 🐳 Конфигурации запуска

Проект поддерживает две конфигурации Docker Compose, выбор осуществляется через переменную `COMPOSE_FILE` в `.env`:

### Base (`docker-compose.base.yaml`)
Минимальная конфигурация без Outbox pattern и Redis для Chat-service.

Состав:
- Nginx, KrakenD, Frontend
- Chat-service + PostgreSQL
- Users-service + PostgreSQL + Redis
- Media-service + PostgreSQL + ClamAV

Подходит для: ограниченных ресурсов, когда гарантированная доставка файлов через очередь не требуется.

```env
COMPOSE_FILE=docker-compose.base.yaml
```

### Extended (`docker-compose.extended.yaml`)
Полная конфигурация с Outbox pattern, RabbitMQ и Redis для Chat-service.

Дополнительно к base:
- RabbitMQ
- Outbox producer воркер
- Outbox consumer воркер
- Prometheus + Loki + Grafana (мониторинг и логи)

Подходит для: production, когда важна гарантированная доставка медиафайлов через очередь.

```env
COMPOSE_FILE=docker-compose.extended.yaml
```

---

## 📈 Мониторинг и логи (VPS)

В extended-конфигурации Prometheus/Loki/Grafana публикуются **только на `127.0.0.1`**, поэтому на VPS они недоступны напрямую из интернета.

### Как открыть Grafana/Prometheus/Loki через SSH-туннель

Запусти туннель с локальной машины (замени `user@your-vps`):

```bash
# Grafana (localhost:3000)
ssh -L 3000:127.0.0.1:3000 user@your-vps

# Prometheus (localhost:9090)
ssh -L 9090:127.0.0.1:9090 user@your-vps

# Loki (localhost:3100)
ssh -L 3100:127.0.0.1:3100 user@your-vps
```

После этого открывай:
- Grafana: `http://localhost:3000`
- Prometheus: `http://localhost:9090`
- Loki: `http://localhost:3100`

---

## 🔌 API

| Сервис        | Порт | Описание         |
|---------------|------|------------------|
| Nginx         | 80   | Точка входа      |
| KrakenD       | 8080 | API Gateway      |
| Chat-service  | 8001 | REST + WebSocket |
| Users-service | 8002 | Аутентификация   |
| Media-service | 8003 | Загрузка файлов  |

WebSocket подключение: `ws://{SERVER_NAME}/ws/api/v1/real_time_chat/ws/{user_id}`

# 💬 RealTimeChat

Мессенджер реального времени на основе WebSockets с регистрацией/аутентификацией и обмена медиафайлами.

## 🌐 Попробовать
**http://176.12.67.28/**

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

## 🛠️ Стек

| Слой | Технологии |
|---|---|
| Frontend | Vue 3 + Vite + Axios |
| Backend | FastAPI + WebSockets + Dishka DI |
| API Gateway | KrakenD |
| БД | PostgreSQL + SQLAlchemy (async) + Alembic |
| Кэш | Redis |
| Очереди | RabbitMQ (Outbox pattern) |
| Хранилище | S3 (Selectel) |
| Балансировщик | Nginx |
| Контейнеризация | Docker + Docker Compose |

---

## ✅ Преимущества

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

# 3. Добавить пользователя в группу docker
sudo usermod -aG docker $USER
newgrp docker

# 4. Запустить
docker compose up --build
```

### Переменные окружения

| Переменная | Описание |
|---|---|
| `SERVER_NAME` | IP или домен сервера |
| `RTCHAT_DB_*` | Настройки БД Chat-service |
| `USERS_DB_*` | Настройки БД Users-service |
| `MEDIA_DB_*` | Настройки БД Media-service |
| `MEDIA_S3_*` | Настройки S3 хранилища |
| `MEDIA_RABBITMQ_*` | Настройки RabbitMQ |

---

## 📋 TODO

### 🔒 Безопасность
- [ ] Блокировать запросы к `.env`, `.git`, `.php` на уровне Nginx — `return 444`
- [ ] Rate limiting по IP для подозрительных паттернов
- [ ] Fail2ban на повторяющиеся атаки с одного IP

### 💬 Chat-service
- [ ] Чат-группы — переделать модель `chat_rooms` и репозиторий
- [ ] Кэш последних 100 сообщений через Redis
- [ ] WebSocket — повторные соединения при разрыве
- [ ] При разлогинивании помечать пользователя офлайн

### 👤 Users-service
- [ ] Обновить архитектуру сервиса
- [ ] Расширить логирование headers в middleware

### 🖼️ Media-service
- [ ] Очистка осиротевших файлов (TTL для непривязанных)
- [ ] Поддержка аватарок пользователей

### ⚡ Производительность
- [ ] Кэширование межсервисных запросов (авторизация в Chat-service)
- [ ] Пагинация истории сообщений

# Media Service

Микросервис для управления медиафайлами в проекте Notes Pet.

## 📋 Описание

Media Service отвечает за загрузку, хранение, валидацию и управление медиафайлами (изображения, видео, аудио, аватары). Сервис обеспечивает безопасную обработку файлов с проверкой на вирусы, валидацией типов и размеров, а также асинхронную загрузку в S3-совместимое хранилище с использованием Transactional Outbox Pattern.

## 🎯 Основные функции

- **Загрузка файлов** - прием и валидация медиафайлов через REST API
- **Проверка безопасности** - сканирование на вирусы через ClamAV
- **Валидация** - проверка типов файлов, размеров, расширений
- **Хранение** - загрузка в S3-совместимое хранилище (Selectel)
- **Метаданные** - сохранение информации о файлах в PostgreSQL
- **Асинхронная обработка** - использование Transactional Outbox Pattern для надежной доставки
- **Трассировка** - интеграция с OpenTelemetry и Jaeger
- **Dependency Injection** - использование Dishka для управления зависимостями

## 🏗️ Архитектура

```
┌─────────────────────────────────────────────────────────────┐
│                    1. API Service (FastAPI)                 │
│  - Принимает файлы                                          │
│  - Валидация и сканирование на вирусы                       │
│  - Загружает в temp S3                                      │
│  - Сохраняет metadata + outbox message (транзакция)         │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    PostgreSQL Database                      │
│  ┌──────────────────┐  ┌──────────────────┐                 │
│  │ files_metadata   │  │ files_outbox     │                 │
│  └──────────────────┘  └──────────────────┘                 │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│              2. Outbox Worker (Message Relay)               │
│  - Polling outbox table каждые N секунд                     │
│  - Публикует сообщения в RabbitMQ                           │
│  - Удаляет/помечает обработанные сообщения                  │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                        RabbitMQ                             │
│  Queue: file.upload.started                                 │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│              3. File Processor Worker (Consumer)            │
│  - Слушает RabbitMQ очередь                                 │
│  - Переносит файл: temp → permanent S3                      │
│  - Обновляет metadata в БД                                  │
└─────────────────────────────────────────────────────────────┘
```

## 🚀 Технологии

- **Python 3.14** - основной язык
- **FastAPI** - веб-фреймворк
- **SQLAlchemy 2.0** - ORM для работы с БД
- **Alembic** - миграции БД
- **PostgreSQL 17** - основная БД
- **RabbitMQ** - брокер сообщений
- **aio-pika** - async клиент для RabbitMQ
- **S3 (Selectel)** - объектное хранилище
- **aioboto3** - async клиент для S3
- **ClamAV** - антивирусное сканирование
- **Pydantic** - валидация данных
- **Dishka** - dependency injection
- **OpenTelemetry** - трассировка
- **Jaeger** - визуализация трейсов
- **Docker** - контейнеризация

## 📦 Поддерживаемые типы файлов

### Изображения (для заметок)
- Форматы: JPEG, PNG, GIF, BMP, WebP, SVG, ICO
- Максимальный размер: 30 MB
- Максимальное разрешение: 3160x3160

### Видео (для заметок)
- Форматы: MP4, MPEG, AVI, MOV, WMV, FLV, WebM, MKV
- Максимальный размер: 500 MB
- Максимальное разрешение: 3160x3160

### Аудио (для заметок)
- Форматы: MP3, WAV, OGG
- Максимальный размер: 30 MB

### Аватары (для пользователей)
- Форматы: JPEG, PNG, GIF, BMP, WebP, SVG, ICO
- Максимальный размер: 5 MB
- Максимальное разрешение: 1024x1024

## 🔌 API Endpoints

### Основные эндпоинты

```http
GET    /api/v1/media_service/health_check/
POST   /api/v1/media_service/upload
GET    /api/v1/media_service/files/{file_uuid}/
GET    /api/v1/media_service/files/{file_uuid}/view/
DELETE /api/v1/media_service/files/delete/{file_uuid}/
```

### Пример загрузки файла

```bash
curl -X POST "http://localhost:8003/api/v1/media_service/upload" \
  -F "file=@image.jpg" \
  -F "upload_context=post_attachment" \
  -F "entity_id=123"
```

## 🛠️ Установка и запуск

### Требования

- Docker и Docker Compose
- Доступ к S3-совместимому хранилищу
- PostgreSQL 17
- RabbitMQ
- ClamAV

### Переменные окружения

Создайте файл `.env`:

```env
# Application
MEDIA_APP_MODE=DEV
MEDIA_APP_HOST=0.0.0.0
MEDIA_APP_PORT=8003

# Database
MEDIA_DB_HOST=localhost
MEDIA_DB_PORT=5432
MEDIA_DB_USER=user
MEDIA_DB_PWD=password
MEDIA_DB_NAME=files_metadata_db

# S3 Storage
MEDIA_S3_ACCESSKEY=your_access_key
MEDIA_S3_SECRETKEY=your_secret_key
MEDIA_S3_ENDPOINTURL=https://s3.example.com
MEDIA_S3_BUCKETNAME=your_bucket

# RabbitMQ
MEDIA_RABBITMQ_HOST=localhost
MEDIA_RABBITMQ_PORT=5672
MEDIA_RABBITMQ_LOGIN=user
MEDIA_RABBITMQ_PASSWORD=password

# Outbox Worker
MEDIA_OUTBOX_ENABLED=True
MEDIA_OUTBOX_POLLING_INTERVAL=1.0
```

### Запуск через Docker Compose

```bash
# Запуск всех сервисов
docker-compose up -d

# Просмотр логов
docker-compose logs -f notes-media

# Остановка
docker-compose down
```

### Локальный запуск (для разработки)

```bash
# Установка зависимостей
pip install -r requirements.txt

# Применение миграций
alembic upgrade head

# Запуск API
python main.py

# Запуск Outbox Worker (в отдельном терминале)
python -m application.outbox_worker

# Запуск File Processor Worker (в отдельном терминале)
python -m application.file_process_worker.main
```

## 📊 Мониторинг

- **API**: http://localhost:8003
- **API Docs**: http://localhost:8003/docs
- **Jaeger UI**: http://localhost:16686
- **RabbitMQ Management**: http://localhost:15672

## 🔄 Transactional Outbox Pattern

Сервис использует паттерн Transactional Outbox для гарантированной доставки сообщений:

### Процесс загрузки файла:

1. **API Service**:
   - Валидирует и сканирует файл на вирусы
   - Загружает файл во временную папку S3 (`temp/`)
   - Сохраняет метаданные файла и сообщение в outbox в одной транзакции

2. **Outbox Worker**:
   - Периодически сканирует таблицу `files_outbox`
   - Публикует найденные сообщения в RabbitMQ
   - Удаляет успешно отправленные сообщения

3. **File Processor Worker**:
   - Слушает очередь RabbitMQ `file.upload.started`
   - Переносит файл из `temp/` в постоянную папку
   - Обновляет метаданные в БД (статус, S3 URL)

### Преимущества:
- ✅ Атомарность операций (БД + сообщение)
- ✅ Гарантированная доставка сообщений
- ✅ Отказоустойчивость (если RabbitMQ недоступен, сообщения сохраняются в БД)
- ✅ Независимое масштабирование компонентов

## 🗄️ Структура БД

### Таблица `files_metadata_orms`
- `id` - первичный ключ
- `file_id` - UUID файла (уникальный индекс)
- `filename` - имя файла
- `size` - размер в байтах
- `content_type` - MIME тип
- `category` - категория (video/image/audio/avatar)
- `status` - статус файла
- `s3_url` - URL файла в S3
- `created_at_db` - дата создания
- `updated_at_db` - дата обновления

### Таблица `files_outbox_orms`
- `id` - первичный ключ
- `message_name` - тип сообщения
- `body` - JSONB с данными
- `status` - статус (PENDING/SENT/FAILED)
- `retry_count` - количество попыток
- `created_at` - дата создания

## 🏛️ Архитектурные паттерны

### Clean Architecture
- **Use Cases** - бизнес-логика (ProcessFileUseCase, UploadFileUseCase, DeleteFileUseCase)
- **Repositories** - работа с данными (FileRepository, FilesOutboxRepository)
- **Services** - вспомогательные сервисы (S3Client, ClamavVirusScanner, FileValidator)

### Dependency Injection (Dishka)
- Автоматическое управление зависимостями
- Разделение на Scopes (APP, REQUEST)
- Легкое тестирование и замена компонентов

### Transactional Outbox
- Гарантированная доставка сообщений
- Атомарность операций
- Отказоустойчивость

## 📝 Логирование

Логи пишутся в:
- Консоль (stdout)
- Файл `logs/media_service.log`

Префиксы логов:
- `[Upload]` - загрузка файлов
- `[ProcessFile]` - обработка файлов
- `[UploadFile]` - сохранение метаданных
- `[DeleteFile]` - удаление файлов
- `[S3]` - операции с S3
- `[FileProcessor]` - обработка сообщений из RabbitMQ
- `[OutboxWorker]` - публикация сообщений в RabbitMQ

## 🔐 Безопасность

- Проверка файлов на вирусы через ClamAV
- Валидация MIME типов и расширений
- Ограничение размеров файлов
- Проверка целостности файлов через python-magic
- Изоляция временных файлов
- UUID для идентификации файлов

## 📄 Лицензия

Проект разработан в рамках учебного проекта Notes Pet.

## 👥 Контакты

Для вопросов и предложений создавайте issue в репозитории.

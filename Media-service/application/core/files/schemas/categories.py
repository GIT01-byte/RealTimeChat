from pydantic import BaseModel, Field


class FileCategory(BaseModel):
    name: str
    content_types: tuple[str, ...]
    extensions: tuple[str, ...]
    max_size: int = Field(gt=0)
    max_width: int | None = None
    max_height: int | None = None

    class Config:
        frozen = True


# Экземпляры категорий файлов
MESSAGE_VIDEOS = FileCategory(
    name="message_video",
    content_types=(
        "video/mp4",
        "video/mpeg",
        "video/x-msvideo",
        "video/quicktime",
        "video/x-ms-wmv",
        "video/x-flv",
        "video/webm",
        "video/x-matroska",
    ),
    extensions=("mp4", "mpeg", "avi", "mov", "wmv", "flv", "webm", "mkv"),
    max_size=500 * 1024 * 1024,  # 500 MB
    max_width=3160,
    max_height=3160,
)

MESSAGE_IMAGES = FileCategory(
    name="message_image",
    content_types=(
        "image/jpeg",
        "image/png",
        "image/gif",
        "image/bmp",
        "image/webp",
        "image/svg+xml",
        "image/x-icon",
        "image/vnd.microsoft.icon",
    ),
    extensions=("jpg", "jpeg", "png", "gif", "bmp", "webp", "svg", "ico"),
    max_size=30 * 1024 * 1024,  # 30 MB
    max_width=3160,
    max_height=3160,
)

MESSAGE_AUDIO = FileCategory(
    name="message_audio",
    content_types=("audio/mpeg", "audio/wav", "audio/wave", "application/ogg"),
    extensions=("mpeg", "mp3", "wav", "ogg"),
    max_size=30 * 1024 * 1024,  # 30 MB
)

USERS_AVATARS = FileCategory(
    name="users_avatar",
    content_types=(
        "image/jpeg",
        "image/png",
        "image/gif",
        "image/bmp",
        "image/webp",
        "image/svg+xml",
        "image/x-icon",
        "image/vnd.microsoft.icon",
    ),
    extensions=("jpg", "jpeg", "png", "gif", "bmp", "webp", "svg", "ico"),
    max_size=5 * 1024 * 1024,  # 5 MB
    max_width=1024,
    max_height=1024,
)

# Маппинг для быстрого доступа
CATEGORIES_BY_NAME: dict[str, FileCategory] = {
    "message_video": MESSAGE_VIDEOS,
    "message_image": MESSAGE_IMAGES,
    "message_audio": MESSAGE_AUDIO,
    "users_avatar": USERS_AVATARS,
}

CHAT_MESSAGE_FILES_NAME = "chat_message_files"
USERS_AVATAR_NAME = "users_avatars"

SOURCE_SERVICE = "RealTimeChat"

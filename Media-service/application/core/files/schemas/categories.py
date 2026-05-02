import os

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


def _parse_bool(value: str | None) -> bool:
    if value is None:
        return False
    return value.strip().lower() in {"1", "true", "yes", "y", "on"}


def _parse_extensions(value: str | None) -> tuple[str, ...] | None:
    """
    Accepts comma/space separated list. Examples:
    - "jpg,jpeg,png"
    - "jpg jpeg png"
    - ".jpg, .png"
    """
    if not value:
        return None
    parts: list[str] = []
    for raw in value.replace(";", ",").replace(" ", ",").split(","):
        item = raw.strip().lower().lstrip(".")
        if item:
            parts.append(item)
    # de-dup, keep order
    uniq: list[str] = []
    for p in parts:
        if p not in uniq:
            uniq.append(p)
    return tuple(uniq) if uniq else None


def _parse_content_types(value: str | None) -> tuple[str, ...] | None:
    """
    Accepts comma/space separated list. Examples:
    - "image/jpeg,image/png"
    - "video/mp4 video/webm"
    """
    if not value:
        return None
    parts: list[str] = []
    for raw in value.replace(";", ",").replace(" ", ",").split(","):
        item = raw.strip().lower()
        if item:
            parts.append(item)
    uniq: list[str] = []
    for p in parts:
        if p not in uniq:
            uniq.append(p)
    return tuple(uniq) if uniq else None


def _parse_int(value: str | None) -> int | None:
    if value is None:
        return None
    value = value.strip()
    if not value:
        return None
    return int(value)


def _category_env_key(category_name: str, suffix: str) -> str:
    # Backward-compatible key (legacy flat style).
    # Example: MEDIA_CATEGORIES_MESSAGE_IMAGE_MAX_SIZE_MB
    return f"MEDIA_CATEGORIES_{category_name.upper()}_{suffix}"


def _category_env_key_nested(category_name: str, suffix: str) -> str:
    # New key style aligned with pydantic-settings config:
    # env_prefix="MEDIA__", env_nested_delimiter="__"
    # Example: MEDIA__CATEGORIES__MESSAGE_IMAGE__MAX_SIZE_MB
    return f"MEDIA__CATEGORIES__{category_name.upper()}__{suffix}"


def _get_category_env(category_name: str, suffix: str) -> str | None:
    """
    Prefer new nested keys, fallback to legacy flat keys.
    This lets overrides work for both:
    - MEDIA__CATEGORIES__MESSAGE_IMAGE__MAX_SIZE_MB
    - MEDIA_CATEGORIES_MESSAGE_IMAGE_MAX_SIZE_MB
    """
    return os.getenv(_category_env_key_nested(category_name, suffix)) or os.getenv(
        _category_env_key(category_name, suffix)
    )


def _override_category_from_env(category: FileCategory) -> FileCategory:
    """
    Overrides a subset of category rules from env.

    Supported env vars (per category name):
    - MEDIA_CATEGORIES_<NAME>_MAX_SIZE_BYTES
    - MEDIA_CATEGORIES_<NAME>_MAX_SIZE_MB
    - MEDIA_CATEGORIES_<NAME>_EXTENSIONS   (comma/space separated)
    - MEDIA_CATEGORIES_<NAME>_CONTENT_TYPES (comma/space separated)
    - MEDIA_CATEGORIES_<NAME>_MAX_WIDTH
    - MEDIA_CATEGORIES_<NAME>_MAX_HEIGHT

    Example:
    - MEDIA_CATEGORIES_MESSAGE_IMAGE_MAX_SIZE_MB=50
    - MEDIA_CATEGORIES_MESSAGE_IMAGE_EXTENSIONS=jpg,jpeg,png,webp
    - MEDIA_CATEGORIES_MESSAGE_IMAGE_CONTENT_TYPES=image/jpeg,image/png
    - MEDIA_CATEGORIES_MESSAGE_IMAGE_MAX_WIDTH=4000
    """
    max_size_bytes = _parse_int(_get_category_env(category.name, "MAX_SIZE_BYTES"))
    max_size_mb = _parse_int(_get_category_env(category.name, "MAX_SIZE_MB"))
    extensions = _parse_extensions(_get_category_env(category.name, "EXTENSIONS"))
    content_types = _parse_content_types(_get_category_env(category.name, "CONTENT_TYPES"))
    max_width = _parse_int(_get_category_env(category.name, "MAX_WIDTH"))
    max_height = _parse_int(_get_category_env(category.name, "MAX_HEIGHT"))

    new_max_size = category.max_size
    if max_size_bytes is not None:
        new_max_size = max_size_bytes
    elif max_size_mb is not None:
        new_max_size = max_size_mb * 1024 * 1024

    return FileCategory(
        name=category.name,
        content_types=content_types if content_types is not None else category.content_types,
        extensions=extensions if extensions is not None else category.extensions,
        max_size=new_max_size,
        max_width=max_width if max_width is not None else category.max_width,
        max_height=max_height if max_height is not None else category.max_height,
    )


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

_DEFAULT_CATEGORIES_BY_NAME: dict[str, FileCategory] = {
    "message_video": MESSAGE_VIDEOS,
    "message_image": MESSAGE_IMAGES,
    "message_audio": MESSAGE_AUDIO,
    "users_avatar": USERS_AVATARS,
}

_USE_ENV_OVERRIDES = _parse_bool(os.getenv("MEDIA__CATEGORIES__USE_ENV_OVERRIDES"))
if _USE_ENV_OVERRIDES:
    _OVERRIDDEN: dict[str, FileCategory] = {
        name: _override_category_from_env(category)
        for name, category in _DEFAULT_CATEGORIES_BY_NAME.items()
    }
    # Keep backward-compat exports that other modules import directly
    MESSAGE_VIDEOS = _OVERRIDDEN["message_video"]
    MESSAGE_IMAGES = _OVERRIDDEN["message_image"]
    MESSAGE_AUDIO = _OVERRIDDEN["message_audio"]
    USERS_AVATARS = _OVERRIDDEN["users_avatar"]
    CATEGORIES_BY_NAME: dict[str, FileCategory] = _OVERRIDDEN
else:
    # Маппинг для быстрого доступа
    CATEGORIES_BY_NAME: dict[str, FileCategory] = _DEFAULT_CATEGORIES_BY_NAME

CHAT_MESSAGE_FILES_NAME = "chat_message_files"
USERS_AVATAR_NAME = "users_avatars"

SOURCE_SERVICE = "RealTimeChat"

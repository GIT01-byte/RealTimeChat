import os
import sys

current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

from pathlib import Path
import sys
import loguru
from core.settings import settings

# Определяем путь к директории для логов
BASE_DIR = Path(__file__).parent.parent
LOGS_DIR = f"{BASE_DIR}/logs"

logger = loguru.logger

if settings.app.mode != "TEST":
    # Настройка уровня логирования
    logger.remove()
    logger.add(
        f"{LOGS_DIR}/logs.log",
        rotation="10 Mb",
        retention="1 week",
        compression="gz",
        colorize=True,
        backtrace=True,
        diagnose=True,
        enqueue=True,
    )
    # Добавляем обработчик для печати в stdout
    logger.add(sys.stderr)

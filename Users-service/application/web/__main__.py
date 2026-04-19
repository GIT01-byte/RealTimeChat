import uvicorn

from application.configs.settings import settings
from application.infrastructure.logging import logger

if __name__ == "__main__":
    try:
        uvicorn.run(
            "application.web.app:app",
            host=settings.app.host,
            port=settings.app.port,
            reload=settings.app.mode == "DEV",
            log_level="info",
        )
    except Exception as e:
        logger.exception(
            "\nFATAL ERROR: An unexpected error occurred during Uvicorn startup. Details: ",
            exc_info=e,
        )
        print("Press Enter to exit...")
        input()

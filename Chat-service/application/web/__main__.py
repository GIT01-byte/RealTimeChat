import uvicorn

from application.configs.settings import settings

if __name__ == "__main__":
    uvicorn.run(
        "application.web.app:app",
        host=settings.app.host,
        port=settings.app.port,
        reload=settings.app.mode == "DEV",
        log_level="info",
    )

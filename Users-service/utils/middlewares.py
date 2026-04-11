import time
from typing import Callable

from fastapi import FastAPI, Request, Response, status
from fastapi.responses import JSONResponse
from pydantic import ValidationError

from utils.logging import logger

HEADERS_DEV = {
    "content-type",
    "content-length",
    "user-agent",
    "origin",
    "upgrade",
    "x-forwarded-for",
    "x-request-id",
}
HEADERS_PROD = {
    "content-type",
    "content-length",
    "x-forwarded-for",
    "x-real-ip",
    "x-request-id",
}


def register_errors_handlers(app: FastAPI) -> None:
    @app.exception_handler(ValidationError)
    async def handle_pydantic_validation_errors(
        request: Request,
        exc: ValidationError,
    ):
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            content={
                "message": "Unhandled error",
                "error": exc.errors(),
            },
        )


def register_dev_log_middleware(app: FastAPI) -> None:
    @app.middleware("http")
    async def dev_log_middleware(request: Request, call_next: Callable):
        start = time.perf_counter()
        request_body = await request.body()  # Тело запроса
        try:
            # Пробуем декодировать тело запроса как JSON
            request_body_decoded = request_body.decode("utf-8")
        except UnicodeDecodeError as e:
            logger.warning(f"Cannot decode request body to UTF-8: {e}")
            request_body_decoded = str(request_body)
        except Exception as e:
            logger.warning(f"Unexpected error during request body decoding: {e}")
            request_body_decoded = str(request_body)

        request_headers = {
            k: v for k, v in request.headers.items() if k.lower() in HEADERS_DEV
        }
        if "authorization" in request.headers:
            request_headers["authorization"] = "<mask>"

        # Выполняем response
        response = await call_next(request)
        response_headers = {
            k: v for k, v in response.headers.items() if k.lower() in HEADERS_DEV
        }

        # Чтение тела ответа response
        response_body = b""
        async for chunk in response.body_iterator:
            response_body += chunk

        # Формируем строку
        end = time.perf_counter() - start
        full_info = (
            "\n--- Request ---\n"
            f"Method: {request.method}\n"
            f"URL: {str(request.url)}\n"
            f"Headers: {request_headers}\n"
            f"Body: {request_body_decoded}\n\n"
            "--- Response ---\n"
            f"Status code: {response.status_code}\n"
            f"Headers: {response_headers}\n"
            f"Media_type: {response.media_type}\n"
            f"Body: {response_body.decode('utf-8')}\n"
            f"Response time: {end:4f} seconds\n"
        )

        # Логируем
        logger.debug(full_info)

        return Response(
            content=response_body,
            status_code=response.status_code,
            headers=dict(response.headers),
            media_type=response.media_type,
        )


def register_prod_log_middleware(app: FastAPI) -> None:
    @app.middleware("http")
    async def prod_log_middleware(request: Request, call_next: Callable):
        start = time.perf_counter()
        request_headers = {
            k: v for k, v in request.headers.items() if k.lower() in HEADERS_PROD
        }

        # Выполняем response
        response = await call_next(request)
        response_headers = {
            k: v for k, v in response.headers.items() if k.lower() in HEADERS_PROD
        }

        # Формируем строку
        end = time.perf_counter() - start
        full_info = (
            "\n--- Request ---\n"
            f"Method: {request.method}\n"
            f"URL: {str(request.url)}\n"
            f"Headers: {request_headers}\n"
            "--- Response ---\n"
            f"Status code: {response.status_code}\n"
            f"Headers: {response_headers}\n"
            f"Response time: {end:4f} seconds"
        )

        # Логируем
        if response.status_code >= 500:
            logger.error(full_info)
        elif response.status_code >= 400:
            logger.warning(full_info)
        else:
            logger.info(full_info)

        return response

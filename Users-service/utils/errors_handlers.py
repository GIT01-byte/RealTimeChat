from fastapi import FastAPI, Request, status
from fastapi.responses import ORJSONResponse
from pydantic import ValidationError


def register_errors_handlers(app: FastAPI) -> None:
    @app.exception_handler(ValidationError)
    async def handle_pydantic_validation_errors(
        request: Request,
        exc: ValidationError,
    ):
        return ORJSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            content={
                "message": "Unhandled error",
                "error": exc.errors(),
            },
        )

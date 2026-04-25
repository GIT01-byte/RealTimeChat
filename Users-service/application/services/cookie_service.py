from application.configs.settings import settings
from application.exceptions.exceptions import (
    SetCookieFailedError,
)
from application.infrastructure.logging import logger
from application.infrastructure.security import (
    ACCESS_TOKEN_TYPE,
    REFRESH_TOKEN_TYPE,
)
from fastapi import Response


class CookieService:
    def clear_cookie_with_tokens(self, response: Response) -> Response:
        """
        Очищает куки с токенами из ответа.

        :param response: Объект Response FastAPI для установки куки
        :return: Модифицированный ответ
        """
        response.delete_cookie(ACCESS_TOKEN_TYPE)
        response.delete_cookie(REFRESH_TOKEN_TYPE)

        return response

    def set_tokens_cookie(
        self, response: Response, access_token: str, refresh_token: str
    ):
        """
        Устанавливает и обновляет токены в куки с настройками безопасности.

        :param access_token: Access токен для установки
        :param access_token: Refresh токен для установки
        :param response: Объект Response FastAPI для установки куки
        :raise SetCookieFailedError: Если установка куки прошла неудачно
        """
        try:
            # 1. Очищаем куки
            self.clear_cookie_with_tokens(response=response)

            # 2. Устанавляиваем токены в куки
            response.set_cookie(
                key=ACCESS_TOKEN_TYPE,
                value=access_token,
                httponly=True,  # Доступно только через HTTP
                secure=True,  # Используется только по HTTPS
                samesite="strict",  # Предотвращение межсайтового отслеживания
                max_age=settings.jwt.access_token_expire_minutes * 60,
            )
            response.set_cookie(
                key=REFRESH_TOKEN_TYPE,
                value=refresh_token,
                httponly=True,  # Доступно только через HTTP
                secure=True,  # Используется только по HTTPS
                samesite="strict",  # Предотвращение межсайтового отслеживания
                max_age=settings.jwt.refresh_token_expire_days * 60,
            )
        except Exception as exc:
            logger.error(f"Ошибка установки куки: {exc}")
            raise SetCookieFailedError() from exc

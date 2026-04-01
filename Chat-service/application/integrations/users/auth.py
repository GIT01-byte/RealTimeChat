from typing import Any

import httpx
from application.exceptions.exceptions import GetUsersListFailedError
from application.utils.logging import logger
from fastapi import HTTPException, Request, status

from .schemas import UserData

# Изнутри Docker сети обращаемся напрямую к Users-service, минуя KrakenD
KRAKEND_URL = "http://rt_chat-krakend-gateway:8080"


async def get_current_user(request: Request):
    logger.debug("Запрос к эндпоинту /user/self_info/")
    async with httpx.AsyncClient() as client:
        try:
            auth_token = request.headers.get("authorization")

            if not auth_token:
                raise HTTPException(
                    status_code=500, detail="Authorization token missing."
                )

            logger.debug(f"Попытка авторизации через {KRAKEND_URL}/user/self_info/")
            login_response = await client.get(
                f"{KRAKEND_URL}/user/self_info/",
                headers={"Authorization": auth_token},
                follow_redirects=True,
            )

            if login_response.status_code != 200:
                logger.warning(
                    f"Авторизация не удалась: status={login_response.status_code}, body={login_response.text}"
                )
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail=f"Authorization failed: {login_response.text}",
                )

            response_data: dict = login_response.json()
            user = UserData(
                id=response_data["user_db"]["id"],
                username=response_data["user_db"]["username"],
                is_active=response_data["user_db"]["is_active"],
                jti=response_data["jwt_payload"]["jti"],
                access_expire=response_data["jwt_payload"]["exp"],
                iat=response_data["jwt_payload"]["iat"],
            )
            logger.debug(
                f"Пользователь авторизован: id={user.id}, username={user.username!r}"
            )
            return user
        except HTTPException:
            raise
        except httpx.RequestError as exc:
            logger.exception(f"Шлюз недоступен при авторизации: {exc}")
            raise HTTPException(status_code=503, detail=f"Gateway unavailable: {exc}")


async def get_users() -> dict[str, Any]:
    logger.debug("Запрос к эндпоинту /user/get_all_users/")
    async with httpx.AsyncClient() as client:
        try:
            logger.debug(
                f"Попытка получить список пользователей через {KRAKEND_URL}/user/get_all_users/"
            )
            get_response = await client.get(
                f"{KRAKEND_URL}/user/get_all_users/",
                follow_redirects=True,
            )

            if get_response.status_code != 200:
                logger.warning(
                    f"Ошибка получения списка пользователей: status={get_response.status_code}, body={get_response.text}"
                )
                raise GetUsersListFailedError

            data = get_response.json()
            logger.debug(f"Получено пользователей: {len(data.get('users', []))}")
            return data
        except GetUsersListFailedError:
            raise
        except httpx.RequestError as exc:
            logger.exception(f"Шлюз недоступен при получении пользователей: {exc}")
            raise HTTPException(status_code=503, detail=f"Gateway unavailable: {exc}")

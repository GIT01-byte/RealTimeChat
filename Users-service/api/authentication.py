from typing import Annotated, Optional

from core.db import UsersRepo
from core.schemas.users import (
    RefreshRequest,
    TokenResponse,
    UserCreate,
    UserRead,
    UserSelfInfo,
    UserUpdate,
)
from exceptions.base import BaseAPIException
from exceptions.exceptions import (
    EntityNotFoundError,
    InvalidCredentialsError,
    LogoutUserFailedError,
    PasswordRequiredError,
    RefreshUserTokensFailedError,
    RegistrationFailedError,
    RepositoryInternalError,
    UserAlreadyExistsError,
    UserNotFoundError,
)
from fastapi import APIRouter, Depends, Form, Request, Response
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import ValidationError
from services.auth_service import (
    AuthService,
)
from utils.logging import logger
from utils.security import ACCESS_TOKEN_TYPE, decode_access_token
from utils.time_decorator import async_timed_report

from api.auth_deps import (
    get_current_active_user,
)

# Роутеры для аутентификации и разработки
auth = APIRouter(redirect_slashes=False)
auth_usage = APIRouter(redirect_slashes=False)
dev_usage = APIRouter(redirect_slashes=False)


@auth.get("/health_check")
async def health_check():
    return {
        "success": True,
        "service": "Users service",
        "status": "running",
        "version": "0.0.1",
    }


# Вход пользователя с выдачей токенов
@auth.post("/login/", response_model=TokenResponse)
@async_timed_report()
async def auth_login(
    response: Response, form_data: Annotated[OAuth2PasswordRequestForm, Depends()]
):
    try:
        auth_service = AuthService()
        if not form_data.password:
            raise PasswordRequiredError()

        # Авторизация пользователя
        user = await auth_service.authenticate_user(
            response, form_data.username, form_data.password
        )
        if not user:
            raise InvalidCredentialsError()

        return TokenResponse(
            access_token=user.access_token,
            access_expire=user.access_expire,
            refresh_token=user.refresh_token,
        )

    except ValidationError as e:
        logger.error(f"Ошибка валидации RegisterRequest: {e.errors()}")


# Регистрация нового пользователя
@auth.post("/register/")
@async_timed_report()
async def auth_register_user(
    request: Request,
    response: Response,
    username: str = Form(..., min_length=3, max_length=64),
    password: str = Form(..., min_length=8),
    profile: Optional[str] = Form(None),
    avatar_uuid: Optional[str] = Form(None),
):
    try:
        auth_service = AuthService()

        # 1. Проверка на текущего пользователя
        current_user_token = request.cookies.get(ACCESS_TOKEN_TYPE)
        if current_user_token:
            try:
                payload = decode_access_token(current_user_token)

                # Извлечение данных из токена
                if payload.jti and payload.sub:
                    user_id = int(payload.sub)
                    logger.info(
                        f"Авто-выход пользователя {user_id} перед новой регистрацией"
                    )

                    await auth_service.loggout_user_logic(
                        response=response, access_jti=payload.jti, user_id=user_id
                    )
            except (ValueError, TypeError, Exception) as e:
                logger.warning(f"Не удалось выполнить авто-выход: {e}")
                pass

        # 2. Регистрируем нового пользователя
        import json

        profile_dict = None
        if profile:
            try:
                profile_dict = json.loads(profile)
            except json.JSONDecodeError:
                logger.warning(f"Некорректный JSON в profile: {profile}")
                profile_dict = None

        payload = UserCreate(
            username=username,
            profile=profile_dict,
            avatar=str(avatar_uuid),
            password=password,
        )

        new_user = await auth_service.register_user_to_db(payload=payload)

        return {
            "ok": True,
            "user_id": new_user["user_id"],
            "new_username": new_user["new_username"],
            "role": new_user["role"],
            "avatar_uuid": new_user["avatar_uuid"],
        }
    # Обрабатываем уникальные ошибки регистрации и ошибки валидации
    except ValidationError as e:
        logger.error(f"Ошибка валидации RegisterRequest: {e.errors()}")
        raise RegistrationFailedError(detail="Ошибка валидации данных")
    except ValueError as e:
        err_msg = str(e)
        if "уже существует" in err_msg:
            raise UserAlreadyExistsError()
        logger.error(f'Ошибка регистрации, exc_info="{err_msg}"')
        raise RegistrationFailedError(detail=err_msg)
    except Exception as e:
        err_msg = str(e)
        if "уже существует" in err_msg:
            raise UserAlreadyExistsError()
        logger.exception(f"Ошибка регистрации: {e}")
        raise RegistrationFailedError()


# Обновление JWT-токенов
@auth.post("/tokens/refresh/", response_model=TokenResponse)
@async_timed_report()
async def auth_refresh_jwt(
    data: RefreshRequest,
    response: Response,
):
    try:
        auth_service = AuthService()
        # Выполняем обновление токенов
        pair = await auth_service.refresh(
            response=response, raw_token=data.refresh_token
        )
        return TokenResponse(
            access_token=pair.access_token,
            access_expire=pair.access_expire,
            refresh_token=pair.refresh_token,
        )
    except ValidationError as e:
        logger.error(f"Ошибка валидации RegisterRequest: {e.errors()}")
    except EntityNotFoundError:
        raise
    except Exception as ex:
        logger.error(f"Обновление токенов прошло неудачно: {ex}")
        raise RefreshUserTokensFailedError()


# Выход пользователя (разлогинивание)
@auth.post("/logout/")
@async_timed_report()
async def auth_logout_user(
    response: Response,
    current_user: UserSelfInfo = Depends(get_current_active_user),
):
    user_id = current_user.user_db.id
    logger.debug(f"Попытка выхода пользователя user_id={user_id}")
    try:
        auth_service = AuthService()
        await auth_service.loggout_user_logic(
            response=response,
            access_jti=current_user.jwt_payload.jti,
            user_id=user_id,
        )
        logger.info(f"Пользователь user_id={user_id} успешно вышел")
        return {"detail": "Выход выполнен успешно"}
    except BaseAPIException:
        raise
    except Exception as e:
        logger.exception(f"Ошибка при выходе пользователя user_id={user_id}")
        raise LogoutUserFailedError() from e


# Получение информации о себе (авторизованном пользователе)
@auth_usage.get("/me/")
@async_timed_report()
async def auth_user_check_self_info(
    current_user=Depends(get_current_active_user),
):
    return current_user


# Обновленеи текущего пользователя
@auth_usage.patch("/me/", response_model=UserRead)
@async_timed_report()
async def update_current_user(
    data: UserUpdate,
    current_user: UserSelfInfo = Depends(get_current_active_user),
):
    """
    Обновляет данные текущего пользователя.
    Все поля необязательны — обновляются только переданные.
    """
    user_id = current_user.user_db.id
    logger.info(
        f"[API] PATCH /me/ user_id={user_id} data={data.model_dump(exclude_none=True)}"
    )
    try:
        updated = await UsersRepo.update_user(
            user_id=user_id,
            username=data.username,
            avatar=data.avatar,
            profile=data.profile,
        )
        logger.info(f"[API] Пользователь ID={user_id} успешно обновлён")
        return UserRead.model_validate(updated)
    except (EntityNotFoundError, UserNotFoundError, UserAlreadyExistsError):
        raise
    except RepositoryInternalError:
        raise
    except Exception as e:
        logger.exception(
            f"[API] Неожиданная ошибка при обновлении пользователя ID={user_id}: {e}"
        )
        raise RepositoryInternalError("Не удалось обновить пользователя") from e


# Удаление текущего пользователя
@auth_usage.delete("/me/", status_code=204)
@async_timed_report()
async def delete_current_user(
    response: Response,
    current_user: UserSelfInfo = Depends(get_current_active_user),
):
    """
    Удаляет аккаунт текущего пользователя и выполняет выход из системы.
    """
    user_id = current_user.user_db.id
    logger.info(f"[API] DELETE /me/ user_id={user_id}")
    try:
        auth_service = AuthService()
        await auth_service.loggout_user_logic(
            response=response,
            access_jti=current_user.jwt_payload.jti,
            user_id=user_id,
        )
        await UsersRepo.delete_user(user_id=user_id)
        logger.info(f"[API] Пользователь ID={user_id} удалён")
    except (EntityNotFoundError, UserNotFoundError):
        raise
    except RepositoryInternalError:
        raise
    except Exception as e:
        logger.exception(
            f"[API] Неожиданная ошибка при удалении пользователя ID={user_id}: {e}"
        )
        raise RepositoryInternalError("Не удалось удалить пользователя") from e


# Получение всех публичных пользователей
@auth_usage.get("/get_all_users/")
async def get_all_user():
    try:
        logger.info("Попытка получения данных пользователей")
        users = await UsersRepo.get_all_users_data()
        return {"users": users}
    except Exception as e:
        logger.error(f"Ошибка при получении списка пользователей: {e}")
        raise RepositoryInternalError(detail="Failed to get users list")


# Получение публичных пользователей по поисковому запросу
@auth_usage.get("/search/")
async def search_users_test(
    search: str,
):
    logger.debug(f"Поиск пользователей по шаблону: {search!r}")
    try:
        users = await UsersRepo.search_users(search_query=search)
        logger.debug(f"Поиск {search!r}: найдено {len(users)} пользователей")
        return {"users": users}
    except RepositoryInternalError:
        raise
    except Exception as e:
        logger.exception(
            f"Неожиданная ошибка при поиске пользователей по шаблону {search!r}"
        )
        raise RepositoryInternalError("Не удалось выполнить поиск пользователей") from e

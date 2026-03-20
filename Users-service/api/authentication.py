import os
import sys

current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

from typing import Annotated, Optional

from core.db.repositories import UsersRepo
from core.schemas.users import (
    RefreshRequest,
    TokenResponse,
    UserSelfInfo,
)
from exceptions.exceptions import (
    EntityNotFoundError,
    InvalidCredentialsError,
    NotAllowedPermisionError,
    PasswordRequiredError,
    RefreshUserTokensFailedError,
    RegistrationFailedError,
    RepositoryInternalError,
    UserAlreadyExistsError,
)
from fastapi import APIRouter, Depends, File, Form, Request, Response, UploadFile
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
    return {"success": "Note users service started"}


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
    email: Optional[str] = Form(None),
    password: str = Form(..., min_length=8),
    profile: Optional[str] = Form(None),
    avatar_file: Optional[UploadFile] = File(None),
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

        payload = {
            "username": username,
            "email": email,
            "profile": profile_dict,
        }

        new_user = await auth_service.register_user_to_db(
            payload=payload, password=password, avatar_file=avatar_file
        )

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
    current_user=Depends(get_current_active_user),
):
    auth_service = AuthService()
    access_jti = current_user["jti"]
    user_id = current_user["user_id"]
    await auth_service.loggout_user_logic(
        response=response, access_jti=access_jti, user_id=user_id
    )
    return {"detail": "Выход выполнен успешно"}


# Получение информации о себе (авторизованном пользователе)
@auth_usage.get("/me/")
@async_timed_report()
async def auth_user_check_self_info(
    current_user=Depends(get_current_active_user),
):
    return current_user


@auth_usage.get("/all_users")
async def get_all_user(
    current_user: UserSelfInfo = Depends(get_current_active_user),
):
    try:
        auth_service = AuthService()
        logger.info(
            f"Попытка доступа к /all_users пользователем {current_user.user_db.username}"
        )

        role_rights = await auth_service.get_role_rights(current_user.user_db.role)
        if role_rights.user_management.view_all_users:
            users = await UsersRepo.get_all_users()
            return {"users": users}

        logger.warning("Попытка доступа к /all_users без прав администратора")
        raise NotAllowedPermisionError
    except NotAllowedPermisionError:
        raise
    except Exception as e:
        logger.error(f"Ошибка при получении списка пользователей: {e}")
        raise RepositoryInternalError(detail="Failed to get users list")

from typing import Annotated

from application.core.schemas.users import (
    RefreshTokensUseCaseInputDTO,
    RegisterUserUseCaseInputDTO,
    TokenResponse,
    UserRead,
    UserSelfInfo,
    UserUpdate,
)
from application.core.use_cases.refresh_tokens import RefreshTokensUseCase
from application.core.use_cases.register_user import RegisterUserUseCase
from application.exceptions.base import BaseAPIException
from application.exceptions.exceptions import (
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
from application.infrastructure.logging import logger
from application.infrastructure.time_decorator import async_timed_report
from application.repositories.users_repo import UsersRepo
from application.services.users_service import UsersService
from application.web.views.v1.deps import get_current_active_user
from dishka import FromDishka
from fastapi import APIRouter, Depends, Request, Response
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import ValidationError

# Роутеры для аутентификации и разработки
router = APIRouter(redirect_slashes=False)


# TODO add commiter in repo use
@router.get("/health_check")
async def health_check():
    return {
        "success": True,
        "service": "Users service",
        "status": "running",
        "version": "0.0.1",
    }


# Вход пользователя с выдачей токенов
@router.post("/login/", response_model=TokenResponse)
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
@router.post("/register/")
@async_timed_report()
async def auth_register_user(
    data: RegisterUserUseCaseInputDTO,
    request: Request,
    response: Response,
    register_user_uc: FromDishka[RegisterUserUseCase],
):
    try:
        register_user_uc_output = await register_user_uc.execute(
            data=data, request=request, response=response
        )
        return register_user_uc_output
    except BaseAPIException:
        raise
    except Exception as ex:
        logger.error(f"[API] Регистрация пользователя прошла неудачно: {ex}")
        raise RegistrationFailedError() from ex


# Обновление JWT-токенов
@router.post("/tokens/refresh/", response_model=TokenResponse)
@async_timed_report()
async def auth_refresh_jwt(
    data: RefreshTokensUseCaseInputDTO,
    response: Response,
    refresh_tokens_uc: FromDishka[RefreshTokensUseCase],
):
    try:
        refresh_tokens_uc_output = await refresh_tokens_uc.execute(
            data=data, response=response
        )
        return refresh_tokens_uc_output
    except BaseAPIException:
        raise
    except Exception as ex:
        logger.error(f"[API] Регистрация пользователя прошла неудачно: {ex}")
        raise RefreshUserTokensFailedError() from ex


# Выход пользователя (разлогинивание)
@router.post("/logout/")
@async_timed_report()
async def auth_logout_user(
    response: Response,
    users_service: FromDishka[UsersService],
    current_user: UserSelfInfo = Depends(get_current_active_user),
):
    user_id = current_user.user_db.id
    logger.debug(f"Попытка выхода пользователя user_id={user_id}")
    try:
        await users_service.loggout_user(
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
@router.get("/me/")
@async_timed_report()
async def auth_user_check_self_info(
    current_user=Depends(get_current_active_user),
):
    return current_user


# Обновленеи текущего пользователя
@router.patch("/me/", response_model=UserRead)
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
@router.delete("/me/", status_code=204)
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
@router.get("/get_all_users/")
async def get_all_user():
    try:
        logger.info("Попытка получения данных пользователей")
        users = await UsersRepo.get_all_users_data()
        return {"users": users}
    except Exception as e:
        logger.error(f"Ошибка при получении списка пользователей: {e}")
        raise RepositoryInternalError(detail="Failed to get users list")


# Получение публичных пользователей по поисковому запросу
@router.get("/search/")
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

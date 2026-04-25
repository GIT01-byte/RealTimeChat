from typing import Annotated

from application.core.schemas.users import (
    RefreshTokensUCInputDTO,
    RegisterUserUCInputDTO,
    RegisterUserUCOutputDTO,
    TokenResponse,
    UserRead,
    UserSelfInfo,
    UserUpdate,
)
from application.core.use_cases.refresh_tokens import RefreshTokensUseCase
from application.core.use_cases.register_user import RegisterUserUseCase
from application.exceptions.base import BaseAPIException
from application.exceptions.exceptions import (
    InvalidCredentialsError,
    LogoutUserFailedError,
    PasswordRequiredError,
    RefreshUserTokensFailedError,
    RegistrationFailedError,
    RepositoryInternalError,
)
from application.infrastructure.logging import logger
from application.infrastructure.time_decorator import async_timed_report
from application.repositories.users_repo import UsersRepo
from application.services.users_service import UsersService
from application.web.views.v1.deps import get_current_active_user
from dishka.integrations.fastapi import FromDishka, inject
from fastapi import APIRouter, Depends, Request, Response
from fastapi.security import OAuth2PasswordRequestForm

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
@inject
@async_timed_report()
async def auth_login(
    users_service: FromDishka[UsersService],
    response: Response,
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
):
    try:
        if not form_data.password:
            raise PasswordRequiredError()

        # Авторизация пользователя
        users_tokens = await users_service.authenticate_user(
            response, form_data.username, form_data.password
        )
        if not users_tokens:
            raise InvalidCredentialsError()

        return users_tokens
    except BaseAPIException:
        raise
    except Exception as ex:
        logger.error(f"[API] Регистрация пользователя прошла неудачно: {ex}")
        raise RegistrationFailedError() from ex


# Регистрация нового пользователя
@router.post("/register/", response_model=RegisterUserUCOutputDTO)
@inject
@async_timed_report()
async def auth_register_user(
    register_user_uc: FromDishka[RegisterUserUseCase],
    request: Request,
    response: Response,
    data: RegisterUserUCInputDTO,
) -> RegisterUserUCOutputDTO:
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
@inject
@async_timed_report()
async def auth_refresh_jwt(
    refresh_tokens_uc: FromDishka[RefreshTokensUseCase],
    response: Response,
    data: RefreshTokensUCInputDTO,
) -> TokenResponse:
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
@inject
@async_timed_report()
async def auth_logout_user(
    users_service: FromDishka[UsersService],
    response: Response,
    current_user: UserSelfInfo = Depends(get_current_active_user),
):
    user_id = current_user.user_db.id
    try:
        await users_service.loggout_user(
            response=response,
            access_jti=current_user.jwt_payload.jti,
            user_id=user_id,
        )
        return {"detail": "Logout succesfull"}
    except BaseAPIException:
        raise
    except Exception as e:
        logger.exception(f"Ошибка при выходе пользователя user_id={user_id}")
        raise LogoutUserFailedError() from e


# Получение информации о себе (авторизованном пользователе)
@router.get("/me/")
@inject
@async_timed_report()
async def auth_user_check_self_info(
    current_user=Depends(get_current_active_user),
):
    return current_user


# Обновленеи текущего пользователя
@router.patch("/me/", response_model=UserRead)
@inject
@async_timed_report()
async def update_current_user(
    users_repo: FromDishka[UsersRepo],
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
        updated = await users_repo.update_user(
            user_id=user_id,
            username=data.username,
            avatar=data.avatar,
            profile=data.profile,
        )
        logger.info(f"[API] Пользователь ID={user_id} успешно обновлён")
        return UserRead.model_validate(updated)
    except BaseAPIException:
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
@inject
@async_timed_report()
async def delete_current_user(
    users_service: FromDishka[UsersService],
    users_repo: FromDishka[UsersRepo],
    response: Response,
    current_user: UserSelfInfo = Depends(get_current_active_user),
):
    """
    Удаляет аккаунт текущего пользователя и выполняет выход из системы.
    """
    user_id = current_user.user_db.id
    logger.info(f"[API] DELETE /me/ user_id={user_id}")
    try:
        await users_service.loggout_user(
            response=response,
            access_jti=current_user.jwt_payload.jti,
            user_id=user_id,
        )
        await users_repo.delete_user(user_id=user_id)
        logger.info(f"[API] Пользователь ID={user_id} удалён")
    except BaseAPIException:
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
@inject
async def get_all_user(
    users_repo: FromDishka[UsersRepo],
):
    try:
        logger.info("Попытка получения данных пользователей")
        users = await users_repo.get_all_users_data()
        return {"users": users}
    except BaseAPIException:
        raise
    except RepositoryInternalError:
        raise
    except Exception as e:
        logger.error(f"Ошибка при получении списка пользователей: {e}")
        raise RepositoryInternalError(detail="Failed to get users list")


# Получение публичных пользователей по поисковому запросу
@router.get("/search/")
@inject
async def search_users_test(
    search: str,
    users_repo: FromDishka[UsersRepo],
):
    logger.debug(f"Поиск пользователей по шаблону: {search!r}")
    try:
        users = await users_repo.search_users(search_query=search)
        logger.debug(f"Поиск {search!r}: найдено {len(users)} пользователей")
        return {"users": users}
    except BaseAPIException:
        raise
    except RepositoryInternalError:
        raise
    except Exception as e:
        logger.exception(
            f"Неожиданная ошибка при поиске пользователей по шаблону {search!r}"
        )
        raise RepositoryInternalError("Не удалось выполнить поиск пользователей") from e

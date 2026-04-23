import json

from application.core.schemas.users import (
    RegisterUserUseCaseInputDTO,
    RegisterUserUseCaseOutputDTO,
    UserCreate,
)
from application.exceptions.base import BaseAPIException
from application.exceptions.exceptions import (
    RegistrationFailedError,
)
from application.infrastructure.logging import logger
from application.infrastructure.security import (
    ACCESS_TOKEN_TYPE,
    decode_access_token,
    hash_password,
)
from application.repositories.database.commiter import Commiter
from application.repositories.users_repo import UsersRepo
from application.services.users_service import UsersService
from fastapi import Request, Response


class RegisterUserUseCase:
    def __init__(
        self,
        users_repo: UsersRepo,
        users_service: UsersService,
        commiter: Commiter,
    ) -> None:
        self.users_repo = users_repo
        self.users_service = users_service
        self.commiter = commiter

    async def execute(
        self,
        data: RegisterUserUseCaseInputDTO,
        request: Request,
        response: Response,
    ):
        try:
            # 1. Проверка на текущего пользователя
            current_user_token = request.cookies.get(ACCESS_TOKEN_TYPE)
            if current_user_token:
                try:
                    payload = decode_access_token(current_user_token)

                    # Извлечение данных из токена
                    if payload.jti and payload.sub:
                        user_id = int(payload.sub)
                        logger.info(
                            f"[RegisterUser] Авто-выход пользователя {user_id} перед новой регистрацией"
                        )

                        await self.users_service.loggout_user(
                            response=response,
                            access_jti=payload.jti,
                            user_id=user_id,
                        )
                except Exception as e:
                    logger.warning(
                        f"[RegisterUser] Не удалось выполнить авто-выход: {e}"
                    )
                    pass

            # 2. Подготавливаем данные для БД
            profile_dict = None
            if data.profile:
                try:
                    profile_dict = json.loads(data.profile)
                except json.JSONDecodeError:
                    logger.warning(
                        f"[RegisterUser] Некорректный JSON в profile: {data.profile}"
                    )
                    profile_dict = None
            payload = UserCreate(
                username=data.username,
                profile=profile_dict,
                avatar=str(data.avatar_uuid),
                password=data.password,
            )

            # 3. Региструрем пользователя
            new_user = await self._register_user_to_db(payload=payload)

            return new_user
        except BaseAPIException:
            raise
        except Exception as e:
            logger.exception(
                f"[RegisterUser] Неожиданная ошибка регистрации пользователя: {data.username}: {e}"
            )
            raise RegistrationFailedError(
                detail=f"Failed to register user {data.username}"
            ) from e

    async def _register_user_to_db(
        self, payload: UserCreate
    ) -> RegisterUserUseCaseOutputDTO:
        logger.info(f"[RegisterUser] Регистрация пользователя {payload.username!r}")
        try:
            hashed_password = hash_password(payload.password)

            created_user = await self.users_repo.create_user(
                username=payload.username,
                hashed_password=hashed_password,
                avatar=payload.avatar,
                profile=payload.profile,
            )
            if not created_user:
                logger.error(
                    f"[RegisterUser] Пользователь {payload.username!r} не зарегистрирован из-за ошибки БД"
                )
                raise RegistrationFailedError()

            await self.commiter.commit()
            logger.info(
                f"[RegisterUser] Пользователь {payload.username!r} зарегистрирован: "
                f"ID={created_user.id}, роль={created_user.role}, аватар={created_user.avatar}"
            )

            return RegisterUserUseCaseOutputDTO(
                user_id=str(created_user.id),
                new_username=created_user.username,
                role=created_user.role,
                avatar_uuid=created_user.avatar,
            )
        except BaseAPIException:
            await self.commiter.rollback()
            raise
        except Exception as e:
            await self.commiter.rollback()
            logger.exception(
                f"[RegisterUser] Ошибка регистрации {payload.username!r}: {e}"
            )
            raise RegistrationFailedError(
                detail=f"Failed to register user {payload.username}"
            ) from e

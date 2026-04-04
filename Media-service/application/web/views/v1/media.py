import datetime
from uuid import UUID

from dishka.integrations.fastapi import FromDishka, inject
from fastapi import (
    APIRouter,
    Depends,
    Response,
)
from sqlalchemy.ext.asyncio import AsyncSession

from application.configs.settings import settings
from application.core.files.schemas.files import (
    FileMeatadataRead,
    FileProcessUCInputDTO,
    FileUploadUCInputDTO,
)
from application.core.files.use_cases.delete_file import DeleteFileUseCase
from application.core.files.use_cases.process_file import ProcessFileUseCase
from application.core.files.use_cases.upload_file import UploadFileUseCase
from application.exceptions.base import BaseAPIException
from application.exceptions.exceptions import (
    DeleteFileFailedError,
    EmptyFileError,
    FilesUploadFailedError,
    LinkedFileFailedError,
    ViewFileFailedError,
)
from application.repositories.database.commiter import Commiter
from application.repositories.files_repository import FileRepository
from application.utils.logging import logger
from application.web.views.v1.deps import FileUploadInputDTO

router = APIRouter(prefix=settings.api.v1.service, tags=["Media Service"])

# ----- Основные API ендпоинты -----
# | Method | Endpoint | Description | Request body |
# | POST | /upload | Загрузка файла | multipart/form-data (file, bucket/folder_name) |
# | GET | /files/{file_uuid} | Получение метаданных о файле | Возвращает JSON: URL, размер, тип, дату загрузки |
# | GET | /files/{file_uuid}/view | Прямая ссылка или редирект на файл | Позволяет просматривать файл в браузере |
# | DELETE | /files/{file_uuid} | Удаление файла | Удаляет файл из S3 и запись из базы данных |
LOG_PREFIX = "[MediaAPI]"


@router.get("/health_check/")
async def health_check():
    return {"success": "Медиа-сервис запущен"}


@router.post("/upload")
@inject
async def upload_file(
    process_file_uc: FromDishka[ProcessFileUseCase],
    upload_file_uc: FromDishka[UploadFileUseCase],
    data: FileUploadInputDTO = Depends(),
):
    filename = data.file.filename if data.file else "unknown"
    logger.debug(
        f"{LOG_PREFIX} POST /upload filename={filename!r} context={data.upload_context!r}"
    )
    try:
        if not data.file or not data.file.size or not data.file.content_type:
            logger.warning(
                f"{LOG_PREFIX} Попытка загрузки пустого файла filename={filename!r}"
            )
            raise EmptyFileError

        # Шаг 1: Обработка и валидация файла
        process_data = FileProcessUCInputDTO(
            file=data.file, upload_context=data.upload_context, entity_id=data.entity_id
        )
        process_file_output = await process_file_uc.execute(data=process_data)
        logger.debug(
            f"{LOG_PREFIX} Файл обработан filename={filename!r} "
            f"file_id={process_file_output.file_id} category={process_file_output.category!r}"
        )

        # Шаг 2: Загрузка в S3 и сохранение метаданных
        upload_data = FileUploadUCInputDTO(
            file=data.file,
            file_id=process_file_output.file_id,
            entity_id=data.entity_id,
            upload_context=data.upload_context,
            unique_filename=process_file_output.unique_filename,
            size=data.file.size,
            content_type=data.file.content_type,
            category=process_file_output.category,
            s3_temp_upload_key=process_file_output.s3_temp_upload_key,
            s3_upload_key=process_file_output.s3_upload_key,
        )
        upload_file_output = await upload_file_uc.execute(data=upload_data)

        logger.info(
            f"{LOG_PREFIX} Файл загружен filename={filename!r} "
            f"file_id={upload_file_output.file_id} status={upload_file_output.upload_status!r}"
        )

        return {
            "ok": True,
            "message": f"Файл {data.file.filename!r} успешно загружен",
            "status": upload_file_output.upload_status,
            "file": {
                "uuid": str(upload_file_output.file_id),
                "size": upload_file_output.size,
                "content_type": upload_file_output.content_type,
                "category": upload_file_output.category,
            },
        }
    except BaseAPIException:
        raise
    except Exception as e:
        logger.exception(
            f"{LOG_PREFIX} Неожиданная ошибка при загрузке файла filename={filename!r}"
        )
        raise FilesUploadFailedError(detail=f"Unexpected error: {str(e)}") from e


@router.get("/files/{file_uuid}/", response_model=FileMeatadataRead)
@inject
async def get_file(
    session: FromDishka[AsyncSession],
    file_uuid: UUID,
):
    logger.debug(f"{LOG_PREFIX} GET /files/{file_uuid}/")
    file_repo = FileRepository(session=session)
    try:
        file_db = await file_repo.get_files_metadata(file_uuid=file_uuid)
        logger.debug(f"{LOG_PREFIX} Метаданные файла file_uuid={file_uuid} получены")
        return file_db
    except BaseAPIException:
        raise
    except Exception as e:
        logger.exception(
            f"{LOG_PREFIX} Неожиданная ошибка при получении метаданных file_uuid={file_uuid}"
        )
        raise ViewFileFailedError from e


@router.get("/files/{file_uuid}/view/")
@inject
async def view_file_url(
    session: FromDishka[AsyncSession],
    file_uuid: UUID,
):
    logger.debug(f"{LOG_PREFIX} GET /files/{file_uuid}/view/")
    file_meta_repo = FileRepository(session=session)
    try:
        file_db = await file_meta_repo.get_files_metadata(file_uuid=file_uuid)

        if not file_db or not file_db.s3_url:
            logger.warning(f"{LOG_PREFIX} S3 URL отсутствует для file_uuid={file_uuid}")
            raise ViewFileFailedError(detail="S3 URL не найден")

        logger.debug(f"{LOG_PREFIX} Редирект на S3 URL для file_uuid={file_uuid}")
        return Response(status_code=302, headers={"Location": file_db.s3_url})
    except BaseAPIException:
        raise
    except Exception as e:
        logger.exception(
            f"{LOG_PREFIX} Неожиданная ошибка при получении ссылки file_uuid={file_uuid}"
        )
        raise ViewFileFailedError from e


@router.patch("/files/{file_uuid}/link/")
@inject
async def mark_as_linked(
    session: FromDishka[AsyncSession],
    commiter: FromDishka[Commiter],
    file_uuid: UUID,
):
    logger.debug(f"{LOG_PREFIX} PATCH /files/{file_uuid}/link/")
    file_meta_repo = FileRepository(session=session)
    try:
        linked_at = datetime.datetime.utcnow()
        result = await file_meta_repo.mark_as_linked(
            file_id=file_uuid, linked_at=linked_at
        )

        if not result:
            await commiter.rollback()
            logger.warning(
                f"{LOG_PREFIX} Не удалось пометить файл file_uuid={file_uuid} как привязанный"
            )
            raise LinkedFileFailedError

        await commiter.commit()
        logger.info(f"{LOG_PREFIX} Файл file_uuid={file_uuid} помечен как привязанный")
        return {
            "ok": True,
            "message": f"Файл {file_uuid} успешно помечен привязанным",
        }
    except BaseAPIException:
        await commiter.rollback()
        raise
    except Exception as e:
        await commiter.rollback()
        logger.exception(
            f"{LOG_PREFIX} Неожиданная ошибка при привязке файла file_uuid={file_uuid}"
        )
        raise LinkedFileFailedError from e


@router.delete("/files/delete/{file_uuid}/")
@inject
async def delete_file(
    delete_file_uc: FromDishka[DeleteFileUseCase],
    file_uuid: UUID,
):
    logger.debug(f"{LOG_PREFIX} DELETE /files/delete/{file_uuid}/")
    try:
        await delete_file_uc.execute(file_id=file_uuid)
        logger.info(f"{LOG_PREFIX} Файл file_uuid={file_uuid} успешно удалён")
        return {
            "ok": True,
            "message": f"Файл {file_uuid} успешно удален",
        }
    except BaseAPIException:
        raise
    except Exception as e:
        logger.exception(
            f"{LOG_PREFIX} Неожиданная ошибка при удалении файла file_uuid={file_uuid}"
        )
        raise DeleteFileFailedError(detail=f"Unexpected error: {str(e)}") from e


# ----- Вспомогательные API ендпоинты -----

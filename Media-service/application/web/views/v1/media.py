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
    ViewFileFailedError,
)
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
    try:
        if not data.file or not data.file.size or not data.file.content_type:
            logger.warning(
                f"Попытка загрузки пустого файла: {data.file.filename if data.file else 'unknown'}"
            )
            raise EmptyFileError

        logger.info(
            f"[Upload] Начало загрузки файла: {data.file.filename}, "
            f"размер: {data.file.size} bytes, тип: {data.file.content_type}, "
            f"контекст: {data.upload_context}"
        )

        # Шаг 1: Обработка и валидация файла
        process_data = FileProcessUCInputDTO(
            file=data.file, upload_context=data.upload_context, entity_id=data.entity_id
        )
        process_file_output = await process_file_uc.execute(data=process_data)
        logger.info(
            f"[Upload] Файл обработан: {data.file.filename}, "
            f"file_id: {process_file_output.file_id}, категория: {process_file_output.category}"
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
            f"[Upload] Файл успешно загружен: {data.file.filename}, "
            f"file_id: {upload_file_output.file_id}, статус: {upload_file_output.upload_status}"
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
    except EmptyFileError:
        logger.error(
            f"[Upload] Пустой файл: {data.file.filename if data.file else 'unknown'}"
        )
        raise
    except BaseAPIException as e:
        logger.error(
            f"[Upload] Ошибка при загрузке файла {data.file.filename if data.file else 'unknown'}: {e.detail}"
        )
        raise
    except Exception as e:
        logger.exception(
            f"[Upload] Неожиданная ошибка при загрузке файла {data.file.filename if data.file else 'unknown'}: {e}"
        )
        raise FilesUploadFailedError(detail=f"Unexpected error: {str(e)}") from e


@router.get("/files/{file_uuid}/", response_model=FileMeatadataRead)
@inject
async def get_file(
    session: FromDishka[AsyncSession],
    file_uuid: UUID,
):
    file_repo = FileRepository(session=session)
    try:
        file_db = await file_repo.get_files_metadata(file_uuid=file_uuid)
        return file_db

    except BaseAPIException:
        raise
    except Exception as e:
        logger.exception(f"Ошибка при получении метаданных файла: {e}")
        raise ViewFileFailedError from e


@router.get("/files/{file_uuid}/view/")
@inject
async def view_file_urL(
    session: FromDishka[AsyncSession],
    file_uuid: UUID,
):
    file_meta_repo = FileRepository(session=session)
    try:
        file_db = await file_meta_repo.get_files_metadata(file_uuid=file_uuid)

        if not file_db or not file_db.s3_url:
            raise ViewFileFailedError(detail="S3 URL не найден")

        return Response(status_code=302, headers={"Location": file_db.s3_url})
    except BaseAPIException:
        raise
    except Exception as e:
        logger.exception(f"Ошибка при получении ссылки на файл: {e}")
        raise ViewFileFailedError from e


@router.delete("/files/delete/{file_uuid}/")
@inject
async def delete_file(
    delete_file_uc: FromDishka[DeleteFileUseCase],
    file_uuid: UUID,
):
    try:
        logger.info(f"[API Delete] Начало удаления файла: file_uuid: {file_uuid}")

        await delete_file_uc.execute(file_id=file_uuid)

        logger.info(f"[API Delete] Файл успешно удален: file_uuid: {file_uuid}")
        return {
            "ok": True,
            "message": f"Файл {file_uuid} успешно удален",
        }
    except BaseAPIException as e:
        logger.error(f"[API Delete] Ошибка удаления файла {file_uuid}: {e.detail}")
        raise
    except Exception as e:
        logger.exception(
            f"[API Delete] Неожиданная ошибка удаления файла {file_uuid}: {e}"
        )
        raise DeleteFileFailedError(detail=f"Unexpected error: {str(e)}") from e


# ----- Вспомогательные API ендпоинты -----

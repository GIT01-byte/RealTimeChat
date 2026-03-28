from uuid import uuid7

from application.core.files.schemas.files import (
    FileProcessUCInputDTO,
    FileProcessUCOuputDTO,
)
from application.exceptions.base import BaseAPIException
from application.exceptions.exceptions import (
    FileCategoryNotSupportedError,
    FileVirusFound,
    ProcessFileFailedError,
    ValidateFileFailedError,
)
from application.services.file_category_detector import FileCategoryDetector
from application.services.file_name_generator import FileMetadataFenerator
from application.services.file_validator import FileValidator
from application.services.file_virus_scanner import ClamavVirusScanner
from application.utils.logging import logger


class ProcessFileUseCase:
    def __init__(
        self,
        virus_scanner: ClamavVirusScanner,
        file_validator: FileValidator,
        file_category_detector: FileCategoryDetector,
        file_meta_generator: FileMetadataFenerator,
    ) -> None:
        self.virus_scanner = virus_scanner
        self.file_validator = file_validator
        self.file_category_detector = file_category_detector
        self.file_name_generator = file_meta_generator

    async def execute(self, data: FileProcessUCInputDTO) -> FileProcessUCOuputDTO:
        file_id = uuid7()
        try:
            logger.info(
                f"[ProcessFile] Начало обработки файла: {data.file.filename}, "
                f"file_id: {file_id}, контекст: {data.upload_context}"
            )

            # Шаг 1: Сканирование на вирусы
            scan_result = await self.virus_scanner.scan(data.file)
            if not scan_result or not scan_result.is_clean:
                virus_info = f", вирус: {scan_result.virus_name}" if scan_result else ""
                logger.warning(
                    f"[ProcessFile] Вирус обнаружен: {data.file.filename}, file_id: {file_id}{virus_info}"
                )
                raise FileVirusFound(detail=f"Virus detected in file{virus_info}")
            logger.info(f"[ProcessFile] Вирусов не обнаружено: {data.file.filename}")

            # Шаг 2: Определение категории
            category = await self.file_category_detector.detect(
                file=data.file,
                upload_context=data.upload_context,
            )
            print(f"File category: {category}")
            if not category:
                logger.error(
                    f"[ProcessFile] Не удалось определить категорию: {data.file.filename}, file_id: {file_id}"
                )
                raise FileCategoryNotSupportedError(
                    detail=f"Cannot detect category for {data.file.filename}"
                )
            logger.info(
                f"[ProcessFile] Категория определена: {category.name} для {data.file.filename}"
            )

            # Шаг 3: Валидация файла
            validation_report = await self.file_validator.validate_file(
                data.file, category
            )
            if not validation_report.is_valid:
                logger.error(
                    f"[ProcessFile] Валидация провалена: {data.file.filename}, file_id: {file_id}, "
                    f"ошибки: {', '.join(validation_report.errors)}"
                )
                raise ValidateFileFailedError(
                    detail=f"Validation failed: {'; '.join(validation_report.errors)}"
                )
            logger.info(f"[ProcessFile] Валидация пройдена: {data.file.filename}")

            # Шаг 4: Генерация имен файлов
            unigue_filename = await self.file_name_generator.generate_unigue_filename(
                file=data.file, category=category, file_id=file_id
            )
            if not unigue_filename:
                logger.error(
                    f"[ProcessFile] Не удалось сгенерировать уникальное имя: {data.file.filename}, file_id: {file_id}"
                )
                raise ProcessFileFailedError(
                    detail="Failed to generate unique filename"
                )

            s3_temp_upload_key = (
                await self.file_name_generator.generate_s3_temp_upload_key(
                    file=data.file, file_id=file_id
                )
            )
            if not s3_temp_upload_key:
                logger.error(
                    f"[ProcessFile] Не удалось сгенерировать temp S3 key: {data.file.filename}, file_id: {file_id}"
                )
                raise ProcessFileFailedError(
                    detail="Failed to generate S3 temp upload key"
                )

            s3_upload_key = await self.file_name_generator.generate_s3_upload_key(
                upload_context=data.upload_context,
                entity_id=data.entity_id,
                unique_filename=unigue_filename,
            )
            if not s3_upload_key:
                logger.error(
                    f"[ProcessFile] Не удалось сгенерировать S3 upload key: {data.file.filename}, file_id: {file_id}"
                )
                raise ProcessFileFailedError(detail="Failed to generate S3 upload key")

            logger.info(
                f"[ProcessFile] Файл успешно обработан: {data.file.filename}, "
                f"file_id: {file_id}, категория: {category.name}"
            )
            return FileProcessUCOuputDTO(
                validaion_status=True,
                file_id=file_id,
                unique_filename=unigue_filename,
                category=category.name,
                s3_temp_upload_key=s3_temp_upload_key,
                s3_upload_key=s3_upload_key,
            )
        except FileVirusFound:
            logger.error(
                f"[ProcessFile] Вирус в файле: {data.file.filename}, file_id: {file_id}"
            )
            raise
        except (FileCategoryNotSupportedError, ValidateFileFailedError) as e:
            logger.error(
                f"[ProcessFile] Ошибка валидации: {data.file.filename}, file_id: {file_id}, {e.detail}"
            )
            raise
        except BaseAPIException:
            raise
        except Exception as e:
            logger.exception(
                f"[ProcessFile] Неожиданная ошибка: {data.file.filename}, file_id: {file_id}: {e}"
            )
            raise ProcessFileFailedError(
                detail=f"Failed to process file {data.file.filename}: {str(e)}"
            ) from e

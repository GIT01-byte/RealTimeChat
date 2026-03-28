import pyclamd
from fastapi import UploadFile
from pydantic import BaseModel

from application.exceptions.exceptions import (
    BaseAPIException,
    EmptyFileError,
    VirusScanFileFailedError,
)
from application.utils.logging import logger


class ScanResult(BaseModel):
    filename: str
    is_clean: bool
    virus_name: str | None = None


class ClamavVirusScanner:
    def __init__(self):
        try:
            self.cd = pyclamd.ClamdUnixSocket()
            self.cd.ping()
        except Exception as e:
            logger.error(f"Не удалось подключиться к ClamAV: {e}")
            raise VirusScanFileFailedError(
                "[Virus Scanner] Virus scan service is not initialized"
            )

    async def scan(self, file: UploadFile) -> ScanResult:
        try:
            if not file or not file.filename:
                raise EmptyFileError("[Virus Scanner] File is empty or has no name")

            content = await file.read()

            try:
                result = self.cd.scan_stream(content)
            except Exception as e:
                logger.exception(f"[Virus Scanner] Ошибка отправки файла в ClamAV: {e}")
                raise VirusScanFileFailedError(f"Scan failed: {str(e)}")

            await file.seek(0)

            if result:
                status, virus_name = result.get("stream")  # type: ignore
                if status == "FOUND":
                    logger.warning(
                        f"[Virus Scanner] ОБНАРУЖЕН ВИРУС: {file.filename}, Вирус: {virus_name}"
                    )
                    return ScanResult(
                        filename=file.filename,
                        is_clean=False,
                        virus_name=virus_name,
                    )

            logger.info(f"[Virus Scanner] ВИРУСОВ НЕ ОБНАРУЖЕНО: {file.filename}")
            return ScanResult(
                filename=file.filename,
                is_clean=True,
            )
        except BaseAPIException:
            raise
        except Exception as e:
            logger.exception(f"[Virus Scanner] Ошибка сканирования на вирусы: {e}")
            raise VirusScanFileFailedError(detail=f"Internal error: {str(e)}")

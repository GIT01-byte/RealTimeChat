from fastapi import HTTPException, status

import httpx

from .schemas import NSFileUploadRequest, NSFileUploadResponse

from utils.logging import logger


async def MS_upload_file(
    request: NSFileUploadRequest,
) -> NSFileUploadResponse:
    async with httpx.AsyncClient() as client:
        try:
            if not request.file:
                logger.exception(f"Invalid file upload reguest in file: {request}")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid file upload request in file: {request}",
                )
            if not request.upload_context:
                logger.exception(f"Invalid file upload reguest in upload_context: {request}")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid file upload request in upload_context: {request}",
                )
            if not request.entity_id:
                logger.exception(f"Invalid file upload reguest in entity_id: {request}")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid file upload request in entity_id: {request}",
                )
            
            files = {
                "file": (
                    request.file.filename,
                    request.file.file,
                    request.file.content_type,
                )
            }
            logger.info(f"upload_file файл - {request.file.filename}")

            query_params = {
                "upload_context": request.upload_context,
                "entity_id": request.entity_id,
            }
            logger.info(f"upload_file запросил - {query_params}")

            upload_response = await client.post(
                url=f"http://krakend:8080/media_service/upload",
                params=query_params,
                files=files,
                follow_redirects=True,
            )

            if upload_response.status_code != 200:
                logger.exception(f"Upload file failed: {upload_response.text}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Upload file failed: {upload_response.text}",
                )

            response_data = upload_response.json()
            logger.info(f"upload_file обработал - {response_data}")

            return NSFileUploadResponse(
                uuid=response_data["file"]["uuid"],
                s3_url=response_data["file"]["s3_url"],
                content_type=response_data["file"]["content_type"],
                category=response_data["file"]["category"],
                uploaded_at_s3=response_data["file"]["uploaded_at"],
            )
        except httpx.RequestError as exc:
            logger.exception(f"Gateway unavailable: {exc}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Media service unavailable",
            )
        except KeyError as exc:
            logger.exception(f"Invalid response format: {exc}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Invalid response from media service",
            )
        except Exception as exc:
            logger.exception(f"Unexpected error: {exc}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error",
            )


async def MS_get_file(file_uuid: str):
    async with httpx.AsyncClient() as client:
        try:
            get_file_response = await client.post(
                url=f"http://krakend:8080/media_service/files/{file_uuid}/",
                follow_redirects=True,
            )

            if get_file_response.status_code != 200:
                logger.exception(f"Get file failed: {get_file_response.text}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Get file failed: {get_file_response.text}",
                )

            response_data = get_file_response.json()
            logger.info(f"get_file обработал - {response_data}")

            return NSFileUploadResponse(
                uuid=response_data["uuid"],
                s3_url=response_data["s3_url"],
                content_type=response_data["content_type"],
                category=response_data["category"],
                uploaded_at_s3=response_data["created_at"],
            )

        except httpx.RequestError as exc:
            logger.exception(f"Gateway unavailable: {exc}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Media service unavailable",
            )
        except KeyError as exc:
            logger.exception(f"Invalid response format: {exc}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Invalid response from media service",
            )
        except Exception as exc:
            logger.exception(f"Unexpected error: {exc}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error",
            )


async def MS_delete_file(file_uuid: str):
    async with httpx.AsyncClient() as client:
        try:
            delete_file_response = await client.delete(
                url=f"http://krakend:8080/media_service/files/delete/{file_uuid}/",
                follow_redirects=True,
            )

            if delete_file_response.status_code != 200:
                logger.exception(f"Delete file failed: {delete_file_response.text}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Delte file failed: {delete_file_response.text}",
                )

            response_data = delete_file_response.json()
            logger.info(f"delete_file обработал - {response_data}")

            return {
                "ok": response_data["ok"], 
                "message": response_data["message"],
            }

        except httpx.RequestError as exc:
            logger.exception(f"Gateway unavailable: {exc}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Media service unavailable",
            )
        except KeyError as exc:
            logger.exception(f"Invalid response format: {exc}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Invalid response from media service",
            )
        except Exception as exc:
            logger.exception(f"Unexpected error: {exc}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error",
            )

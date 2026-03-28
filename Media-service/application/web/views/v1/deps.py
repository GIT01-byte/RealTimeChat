from fastapi import UploadFile

from application.core.files.schemas.files import UploadContext


class FileUploadInputDTO:
    def __init__(
        self,
        file: UploadFile,
        upload_context: UploadContext,
        entity_id: int,
    ):
        self.file = file
        self.upload_context = upload_context
        self.entity_id = entity_id

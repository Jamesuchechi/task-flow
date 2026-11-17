from pathlib import Path
from uuid import uuid4

from fastapi import UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.cache import invalidate_user_task_cache
from app.core.config import get_settings
from app.core.errors import AppError
from app.db.models import TaskAttachment
from app.services.tasks import TaskService


class AttachmentService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.settings = get_settings()

    async def upload_to_task(
        self,
        task_id: int,
        user_id: int,
        file: UploadFile,
    ) -> TaskAttachment:
        await TaskService(self.db).get_by_id_for_user(task_id, user_id)

        raw_name = file.filename or ""
        safe_name = Path(raw_name).name.strip()
        if not safe_name:
            raise AppError(
                code="INVALID_FILENAME",
                message="Uploaded file must have a valid filename",
                status_code=400,
            )

        ext = Path(safe_name).suffix.lower()
        if ext not in self.settings.allowed_upload_extensions:
            raise AppError(
                code="UNSUPPORTED_FILE_TYPE",
                message=f"File extension '{ext}' is not allowed",
                status_code=400,
            )

        content = await file.read()
        size_bytes = len(content)
        if size_bytes == 0:
            raise AppError(
                code="EMPTY_FILE",
                message="Uploaded file cannot be empty",
                status_code=400,
            )
        if size_bytes > self.settings.max_upload_size_bytes:
            raise AppError(
                code="FILE_TOO_LARGE",
                message=f"File exceeds maximum size of {self.settings.max_upload_size_bytes} bytes",
                status_code=413,
            )

        upload_dir = Path(self.settings.upload_dir)
        upload_dir.mkdir(parents=True, exist_ok=True)
        stored_filename = f"{uuid4().hex}_{safe_name}"
        storage_path = upload_dir / stored_filename
        storage_path.write_bytes(content)

        attachment = TaskAttachment(
            task_id=task_id,
            owner_id=user_id,
            filename=safe_name,
            stored_filename=stored_filename,
            content_type=file.content_type or "application/octet-stream",
            size_bytes=size_bytes,
            storage_path=str(storage_path),
        )
        self.db.add(attachment)
        await self.db.commit()
        await self.db.refresh(attachment)
        await invalidate_user_task_cache(user_id, task_id=task_id)
        return attachment

    async def list_for_task(
        self, task_id: int, user_id: int
    ) -> list[TaskAttachment]:
        await TaskService(self.db).get_by_id_for_user(task_id, user_id)
        result = await self.db.execute(
            select(TaskAttachment)
            .where(
                TaskAttachment.task_id == task_id,
                TaskAttachment.owner_id == user_id,
            )
            .order_by(TaskAttachment.created_at.desc())
        )
        return list(result.scalars().all())

    async def get_for_user(
        self, attachment_id: int, user_id: int
    ) -> TaskAttachment:
        attachment = await self.db.get(TaskAttachment, attachment_id)
        if attachment is None or attachment.owner_id != user_id:
            raise AppError(
                code="ATTACHMENT_NOT_FOUND",
                message="Attachment not found",
                status_code=404,
            )
        return attachment

    async def delete(self, attachment_id: int, user_id: int) -> TaskAttachment:
        attachment = await self.get_for_user(attachment_id, user_id)
        task_id = attachment.task_id
        file_path = Path(attachment.storage_path)

        await self.db.delete(attachment)
        await self.db.commit()

        if file_path.exists():
            file_path.unlink(missing_ok=True)

        await invalidate_user_task_cache(user_id, task_id=task_id)
        return attachment

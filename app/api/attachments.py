from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, File, Path as PathParam, UploadFile, status
from fastapi.responses import FileResponse

from app.core.errors import AppError
from app.core.rate_limit import rate_limit
from app.core.websocket import ws_manager
from app.dependencies import AttachmentServiceDep, CurrentUser
from app.schemas.attachment import AttachmentRead

router = APIRouter(tags=["Attachments"])


@router.post(
    "/tasks/{task_id}/attachments",
    response_model=AttachmentRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[rate_limit(max_requests=30, window_seconds=60)],
)
async def upload_attachment(
    task_id: Annotated[int, PathParam(gt=0)],
    file: Annotated[UploadFile, File(...)],
    service: AttachmentServiceDep,
    current_user: CurrentUser,
    background_tasks: BackgroundTasks,
):
    attachment = await service.upload_to_task(task_id, current_user.id, file)
    background_tasks.add_task(
        ws_manager.send_to_user,
        current_user.id,
        "attachment.uploaded",
        {
            "attachment_id": attachment.id,
            "task_id": task_id,
            "filename": attachment.filename,
        },
    )
    return attachment


@router.get(
    "/tasks/{task_id}/attachments",
    response_model=list[AttachmentRead],
)
async def list_task_attachments(
    task_id: Annotated[int, PathParam(gt=0)],
    service: AttachmentServiceDep,
    current_user: CurrentUser,
):
    return await service.list_for_task(task_id, current_user.id)


@router.get("/attachments/{attachment_id}/download")
async def download_attachment(
    attachment_id: Annotated[int, PathParam(gt=0)],
    service: AttachmentServiceDep,
    current_user: CurrentUser,
):
    attachment = await service.get_for_user(attachment_id, current_user.id)
    file_path = Path(attachment.storage_path)
    if not file_path.exists():
        raise AppError(
            code="FILE_MISSING",
            message="Attachment file is missing from storage",
            status_code=404,
        )
    return FileResponse(
        path=file_path,
        filename=attachment.filename,
        media_type=attachment.content_type,
    )


@router.delete(
    "/attachments/{attachment_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_attachment(
    attachment_id: Annotated[int, PathParam(gt=0)],
    service: AttachmentServiceDep,
    current_user: CurrentUser,
    background_tasks: BackgroundTasks,
):
    attachment = await service.delete(attachment_id, current_user.id)
    background_tasks.add_task(
        ws_manager.send_to_user,
        current_user.id,
        "attachment.deleted",
        {"attachment_id": attachment_id, "task_id": attachment.task_id},
    )
    return None

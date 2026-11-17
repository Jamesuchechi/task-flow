from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Query, status
from fastapi.responses import FileResponse

from app.core.errors import AppError
from app.dependencies import CurrentUser, JobServiceDep
from app.schemas.job import ExportTasksRequest, JobRead, JobStatus, JobType
from app.schemas.pagination import PaginatedResponse
from app.schemas.task import TaskStatus
from app.services.jobs import run_export_tasks_job, run_overdue_digest_job

router = APIRouter(
    prefix="/jobs",
    tags=["Background Jobs"],
)


@router.post(
    "/export-tasks",
    response_model=JobRead,
    status_code=status.HTTP_202_ACCEPTED,
)
async def enqueue_export_tasks(
    service: JobServiceDep,
    current_user: CurrentUser,
    background_tasks: BackgroundTasks,
    body: ExportTasksRequest | None = None,
):
    req = body or ExportTasksRequest()
    if req.format not in {"json", "csv"}:
        raise AppError(
            code="INVALID_EXPORT_FORMAT",
            message="Export format must be 'json' or 'csv'",
            status_code=400,
        )
    if req.status is not None:
        try:
            TaskStatus(req.status)
        except ValueError:
            raise AppError(
                code="INVALID_TASK_STATUS",
                message=f"Invalid task status filter: {req.status}",
                status_code=400,
            )

    job = await service.create_job(
        job_type=JobType.export_tasks,
        owner_id=current_user.id,
        payload={"format": req.format, "status": req.status},
    )
    background_tasks.add_task(
        run_export_tasks_job,
        job.id,
        current_user.id,
        req.format,
        req.status,
    )
    return job


@router.post(
    "/overdue-digest",
    response_model=JobRead,
    status_code=status.HTTP_202_ACCEPTED,
)
async def enqueue_overdue_digest(
    service: JobServiceDep,
    current_user: CurrentUser,
    background_tasks: BackgroundTasks,
):
    job = await service.create_job(
        job_type=JobType.overdue_digest,
        owner_id=current_user.id,
    )
    background_tasks.add_task(run_overdue_digest_job, job.id, current_user.id)
    return job


@router.get(
    "",
    response_model=PaginatedResponse[JobRead],
)
async def list_jobs(
    service: JobServiceDep,
    current_user: CurrentUser,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
):
    return await service.list_user_jobs_paginated(
        user_id=current_user.id,
        page=page,
        page_size=page_size,
    )


@router.get(
    "/{job_id}",
    response_model=JobRead,
)
async def get_job(
    job_id: str,
    service: JobServiceDep,
    current_user: CurrentUser,
):
    return await service.get_for_user(job_id, current_user.id)


@router.get("/{job_id}/download")
async def download_job_export(
    job_id: str,
    service: JobServiceDep,
    current_user: CurrentUser,
):
    job = await service.get_for_user(job_id, current_user.id)
    if job.job_type != JobType.export_tasks:
        raise AppError(
            code="JOB_NOT_DOWNLOADABLE",
            message="Only export_tasks jobs produce downloadable files",
            status_code=400,
        )
    if job.status != JobStatus.completed or not job.result:
        raise AppError(
            code="JOB_NOT_READY",
            message=f"Job is currently '{job.status.value}'",
            status_code=409,
        )

    file_path = Path(job.result["file_path"])
    if not file_path.exists():
        raise AppError(
            code="EXPORT_FILE_MISSING",
            message="Export file is no longer available",
            status_code=404,
        )

    media_type = (
        "text/csv" if job.result.get("format") == "csv" else "application/json"
    )
    return FileResponse(
        path=file_path,
        filename=job.result["filename"],
        media_type=media_type,
    )

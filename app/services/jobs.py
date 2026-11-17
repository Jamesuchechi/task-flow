import csv
import io
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.errors import AppError
from app.core.websocket import ws_manager
from app.db import database
from app.db.models import BackgroundJob, Task
from app.schemas.job import JobRead, JobStatus, JobType
from app.schemas.pagination import PaginatedResponse
from app.schemas.task import TaskStatus


class JobService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def create_job(
        self,
        job_type: JobType,
        owner_id: int,
        payload: dict[str, Any] | None = None,
    ) -> BackgroundJob:
        job = BackgroundJob(
            job_type=job_type,
            status=JobStatus.pending,
            payload=payload or {},
            owner_id=owner_id,
        )
        self.db.add(job)
        await self.db.commit()
        await self.db.refresh(job)
        return job

    async def get_for_user(self, job_id: str, user_id: int) -> BackgroundJob:
        job = await self.db.get(BackgroundJob, job_id)
        if job is None or job.owner_id != user_id:
            raise AppError(
                code="JOB_NOT_FOUND",
                message="Background job not found",
                status_code=404,
            )
        return job

    async def list_user_jobs_paginated(
        self,
        user_id: int,
        page: int = 1,
        page_size: int = 20,
    ) -> PaginatedResponse[JobRead]:
        total = (
            await self.db.execute(
                select(func.count(BackgroundJob.id)).where(
                    BackgroundJob.owner_id == user_id
                )
            )
        ).scalar_one()

        offset = (page - 1) * page_size
        rows = (
            (
                await self.db.execute(
                    select(BackgroundJob)
                    .where(BackgroundJob.owner_id == user_id)
                    .order_by(BackgroundJob.created_at.desc())
                    .offset(offset)
                    .limit(page_size)
                )
            )
            .scalars()
            .all()
        )
        items = [JobRead.model_validate(job) for job in rows]
        return PaginatedResponse[JobRead].create(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
        )


async def run_export_tasks_job(
    job_id: str,
    user_id: int,
    export_format: str = "json",
    status_filter: str | None = None,
) -> None:
    if database.SessionLocal is None:
        return

    settings = get_settings()
    async with database.SessionLocal() as session:
        job = await session.get(BackgroundJob, job_id)
        if job is None:
            return

        job.status = JobStatus.running
        await session.commit()

        try:
            stmt = select(Task).where(Task.owner_id == user_id)
            if status_filter is not None:
                stmt = stmt.where(Task.status == TaskStatus(status_filter))
            stmt = stmt.order_by(Task.created_at.desc())
            tasks = (await session.execute(stmt)).scalars().all()

            export_dir = Path(settings.export_dir)
            export_dir.mkdir(parents=True, exist_ok=True)
            ext = "csv" if export_format == "csv" else "json"
            filename = f"tasks_export_{job_id}.{ext}"
            file_path = export_dir / filename

            if ext == "csv":
                buf = io.StringIO()
                writer = csv.writer(buf)
                writer.writerow(
                    ["id", "title", "description", "status", "due_at", "created_at"]
                )
                for t in tasks:
                    writer.writerow(
                        [
                            t.id,
                            t.title,
                            t.description or "",
                            t.status.value,
                            t.due_at.isoformat() if t.due_at else "",
                            t.created_at.isoformat(),
                        ]
                    )
                file_path.write_text(buf.getvalue(), encoding="utf-8")
            else:
                records = [
                    {
                        "id": t.id,
                        "title": t.title,
                        "description": t.description,
                        "status": t.status.value,
                        "due_at": t.due_at.isoformat() if t.due_at else None,
                        "created_at": t.created_at.isoformat(),
                    }
                    for t in tasks
                ]
                file_path.write_text(
                    json.dumps(records, indent=2), encoding="utf-8"
                )

            job.status = JobStatus.completed
            job.completed_at = datetime.now(UTC)
            job.result = {
                "task_count": len(tasks),
                "format": ext,
                "filename": filename,
                "file_path": str(file_path),
            }
            await session.commit()

            await ws_manager.send_to_user(
                user_id,
                "job.completed",
                {"job_id": job.id, "job_type": job.job_type.value, "result": job.result},
            )
        except Exception as exc:
            job.status = JobStatus.failed
            job.completed_at = datetime.now(UTC)
            job.error = str(exc)
            await session.commit()

            await ws_manager.send_to_user(
                user_id,
                "job.failed",
                {"job_id": job.id, "job_type": job.job_type.value, "error": job.error},
            )


async def run_overdue_digest_job(job_id: str, user_id: int) -> None:
    if database.SessionLocal is None:
        return

    async with database.SessionLocal() as session:
        job = await session.get(BackgroundJob, job_id)
        if job is None:
            return

        job.status = JobStatus.running
        await session.commit()

        try:
            now = datetime.now(UTC)
            tasks = (
                (
                    await session.execute(
                        select(Task).where(Task.owner_id == user_id)
                    )
                )
                .scalars()
                .all()
            )

            overdue = []
            upcoming = []
            for t in tasks:
                if t.status == TaskStatus.done or t.due_at is None:
                    continue
                due = t.due_at if t.due_at.tzinfo else t.due_at.replace(tzinfo=UTC)
                if due < now:
                    overdue.append({"id": t.id, "title": t.title, "due_at": due.isoformat()})
                else:
                    upcoming.append({"id": t.id, "title": t.title, "due_at": due.isoformat()})

            job.status = JobStatus.completed
            job.completed_at = datetime.now(UTC)
            job.result = {
                "total_tasks": len(tasks),
                "overdue_count": len(overdue),
                "upcoming_count": len(upcoming),
                "overdue_tasks": overdue,
                "upcoming_tasks": upcoming,
            }
            await session.commit()

            await ws_manager.send_to_user(
                user_id,
                "job.completed",
                {"job_id": job.id, "job_type": job.job_type.value, "result": job.result},
            )
        except Exception as exc:
            job.status = JobStatus.failed
            job.completed_at = datetime.now(UTC)
            job.error = str(exc)
            await session.commit()

            await ws_manager.send_to_user(
                user_id,
                "job.failed",
                {"job_id": job.id, "job_type": job.job_type.value, "error": job.error},
            )


async def log_task_activity(event: str, task_id: int, user_id: int) -> None:
    """Lightweight background hook for task audit/notification logging."""
    await ws_manager.send_to_user(
        user_id,
        event,
        {"task_id": task_id, "owner_id": user_id},
    )

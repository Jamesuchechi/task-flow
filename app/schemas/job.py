from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict


class JobStatus(StrEnum):
    pending = "pending"
    running = "running"
    completed = "completed"
    failed = "failed"


class JobType(StrEnum):
    export_tasks = "export_tasks"
    overdue_digest = "overdue_digest"


class ExportTasksRequest(BaseModel):
    format: str = "json"  # "json" or "csv"
    status: str | None = None


class JobRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    job_type: JobType
    status: JobStatus
    payload: dict[str, Any] | None = None
    result: dict[str, Any] | None = None
    error: str | None = None
    owner_id: int
    created_at: datetime
    completed_at: datetime | None = None

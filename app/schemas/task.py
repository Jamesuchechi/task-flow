from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field


class TaskStatus(StrEnum):
    todo = "todo"
    in_progress = "in_progress"
    done = "done"


class TaskCreate(BaseModel):

    title: str = Field(
        min_length=1,
        max_length=120
    )

    description: str | None = Field(
        default=None,
        max_length=2000
    )

    status: TaskStatus = TaskStatus.todo

    due_at: datetime | None = None


class TaskUpdate(BaseModel):

    title: str | None = Field(
        default=None,
        min_length=1,
        max_length=120
    )

    description: str | None = Field(
        default=None,
        max_length=2000
    )

    status: TaskStatus | None = None

    due_at: datetime | None = None


class TaskRead(TaskCreate):

    model_config = ConfigDict(
        from_attributes=True
    )

    id: int
    created_at: datetime
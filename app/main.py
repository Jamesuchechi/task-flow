
from datetime import UTC, datetime
from typing import Annotated

from fastapi import FastAPI, Path, Query

from app.schemas.task import TaskCreate, TaskRead, TaskStatus


app = FastAPI(
    title="TaskFlow API",
    description="A task management API built with FastAPI",
    version="0.1.0",
)


# Temporary sample data.
sample_tasks: list[TaskRead] = [
    TaskRead(
        id=1,
        title="Learn FastAPI",
        description="Understand routing and validation",
        status=TaskStatus.in_progress,
        due_at=None,
        created_at=datetime(2026, 10, 20, tzinfo=UTC),
    ),
    TaskRead(
        id=2,
        title="Build the TaskFlow API",
        description="Implement the first endpoints",
        status=TaskStatus.todo,
        due_at=None,
        created_at=datetime(2026, 10, 21, tzinfo=UTC),
    ),
    TaskRead(
        id=3,
        title="Review HTTP fundamentals",
        description=None,
        status=TaskStatus.done,
        due_at=None,
        created_at=datetime(2026, 10, 22, tzinfo=UTC),
    ),
]


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}

@app.post("/tasks", response_model=TaskRead, status_code=201)
async def create_task(task: TaskCreate) -> TaskRead:
    new_task = TaskRead(
        id=len(sample_tasks) + 1,
        created_at=datetime.now(tz=UTC),
        **task.dict(),
    )

    sample_tasks.append(new_task)

    return new_task


@app.get("/tasks", response_model=list[TaskRead])
async def list_tasks(
    status: TaskStatus | None = None,
    q: Annotated[str | None, Query(min_length=2)] = None,
) -> list[TaskRead]:
    results = sample_tasks

    if status is not None:
        results = [
            task for task in results
            if task.status == status
        ]

    if q is not None:
        search_term = q.casefold()

        results = [
            task for task in results
            if search_term in task.title.casefold()
        ]

    return results


@app.get("/tasks/{task_id}", response_model=TaskRead)
async def get_task(
    task_id: Annotated[int, Path(gt=0)],
) -> TaskRead:
    for task in sample_tasks:
        if task.id == task_id:
            return task

    from fastapi import HTTPException, status as http_status

    raise HTTPException(
        status_code=http_status.HTTP_404_NOT_FOUND,
        detail="Task not found",
    )

from typing import Annotated, Literal

from fastapi import APIRouter, BackgroundTasks, Path, Query, Response, status

from app.dependencies import CurrentUser, TaskServiceDep
from app.schemas.pagination import PaginatedResponse
from app.schemas.task import TaskCreate, TaskRead, TaskStatus, TaskUpdate
from app.services.jobs import log_task_activity

router = APIRouter(
    prefix="/tasks",
    tags=["Tasks"],
)


@router.post(
    "",
    response_model=TaskRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_task(
    data: TaskCreate,
    service: TaskServiceDep,
    current_user: CurrentUser,
    background_tasks: BackgroundTasks,
):
    task = await service.create(data, user_id=current_user.id)
    background_tasks.add_task(
        log_task_activity, "task.created", task.id, current_user.id
    )
    return task


@router.get(
    "",
    response_model=PaginatedResponse[TaskRead],
)
async def list_tasks(
    response: Response,
    service: TaskServiceDep,
    current_user: CurrentUser,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
    task_status: Annotated[
        TaskStatus | None,
        Query(alias="status"),
    ] = None,
    q: Annotated[str | None, Query(min_length=2)] = None,
    sort_by: Literal["created_at", "due_at", "title", "status"] = "created_at",
    sort_order: Literal["asc", "desc"] = "desc",
):
    paginated, cache_hit = await service.get_user_tasks_paginated(
        user_id=current_user.id,
        page=page,
        page_size=page_size,
        task_status=task_status,
        q=q,
        sort_by=sort_by,
        sort_order=sort_order,
    )
    response.headers["X-Cache"] = "HIT" if cache_hit else "MISS"
    return paginated


@router.get(
    "/{task_id}",
    response_model=TaskRead,
)
async def get_task(
    task_id: Annotated[int, Path(gt=0)],
    response: Response,
    service: TaskServiceDep,
    current_user: CurrentUser,
):
    task, cache_hit = await service.get_by_id_cached(task_id, current_user.id)
    response.headers["X-Cache"] = "HIT" if cache_hit else "MISS"
    return task


@router.patch(
    "/{task_id}",
    response_model=TaskRead,
)
async def update_task(
    task_id: Annotated[int, Path(gt=0)],
    data: TaskUpdate,
    service: TaskServiceDep,
    current_user: CurrentUser,
    background_tasks: BackgroundTasks,
):
    task = await service.update(task_id, data, user_id=current_user.id)
    background_tasks.add_task(
        log_task_activity, "task.updated", task.id, current_user.id
    )
    return task


@router.delete(
    "/{task_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_task(
    task_id: Annotated[int, Path(gt=0)],
    service: TaskServiceDep,
    current_user: CurrentUser,
    background_tasks: BackgroundTasks,
):
    await service.delete(task_id, user_id=current_user.id)
    background_tasks.add_task(
        log_task_activity, "task.deleted", task_id, current_user.id
    )
    return None

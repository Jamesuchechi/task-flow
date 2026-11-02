
from typing import Annotated

from fastapi import APIRouter, Path, Query, status

from app.dependencies import TaskServiceDep
from app.schemas.task import TaskCreate, TaskRead, TaskStatus, TaskUpdate


router = APIRouter(
    prefix="/tasks",
    tags=["Tasks"]
)


@router.post(
    "",
    response_model=TaskRead,
    status_code=status.HTTP_201_CREATED
)
async def create_task(
    task: TaskCreate,
    service: TaskServiceDep
):
    return await service.create(task)


@router.get(
    "",
    response_model=list[TaskRead]
)
async def list_tasks(
    service: TaskServiceDep,
    task_status: Annotated[
        TaskStatus | None,
        Query(alias="status")
    ] = None,
    q: Annotated[str | None, Query(min_length=2)] = None,
):
    results = await service.get_all()

    if task_status is not None:
        results = [
            task for task in results
            if task.status == task_status
        ]

    if q is not None:
        search_term = q.casefold()

        results = [
            task for task in results
            if search_term in task.title.casefold()
        ]

    return results


@router.get(
    "/{task_id}",
    response_model=TaskRead
)
async def get_task(
    task_id: Annotated[int, Path(gt=0)],
    service: TaskServiceDep
):
    return await service.get_by_id(task_id)


@router.patch(
    "/{task_id}",
    response_model=TaskRead
)
async def update_task(
    task_id: Annotated[int, Path(gt=0)],
    data: TaskUpdate,
    service: TaskServiceDep
):
    return await service.update(task_id, data)


@router.delete(
    "/{task_id}",
    status_code=status.HTTP_204_NO_CONTENT
)
async def delete_task(
    task_id: Annotated[int, Path(gt=0)],
    service: TaskServiceDep
):
    await service.delete(task_id)
    return None

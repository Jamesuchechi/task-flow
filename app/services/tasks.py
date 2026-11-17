from typing import Literal

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.cache import (
    cache,
    invalidate_user_task_cache,
    task_detail_cache_key,
    user_tasks_cache_prefix,
)
from app.core.errors import AppError
from app.db.models import Task
from app.schemas.pagination import PaginatedResponse
from app.schemas.task import TaskCreate, TaskRead, TaskStatus, TaskUpdate

SORT_COLUMNS = {
    "created_at": Task.created_at,
    "due_at": Task.due_at,
    "title": Task.title,
    "status": Task.status,
}


class TaskService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, data: TaskCreate, user_id: int) -> Task:
        task = Task(**data.model_dump(), owner_id=user_id)
        self.db.add(task)
        await self.db.commit()
        await self.db.refresh(task)
        await invalidate_user_task_cache(user_id)
        return task

    async def get_by_id(self, task_id: int) -> Task:
        task = await self.db.get(Task, task_id)
        if task is None:
            raise AppError(
                code="TASK_NOT_FOUND",
                message="Task not found",
                status_code=404,
            )
        return task

    async def get_by_id_for_user(self, task_id: int, user_id: int) -> Task:
        task = await self.get_by_id(task_id)
        if task.owner_id != user_id:
            raise AppError(
                code="TASK_NOT_FOUND",
                message="Task not found",
                status_code=404,
            )
        return task

    async def get_by_id_cached(
        self, task_id: int, user_id: int
    ) -> tuple[TaskRead, bool]:
        cache_key = task_detail_cache_key(task_id)
        cached = await cache.get(cache_key)
        if cached is not None:
            task_read = TaskRead.model_validate(cached)
            if task_read.owner_id != user_id:
                raise AppError(
                    code="TASK_NOT_FOUND",
                    message="Task not found",
                    status_code=404,
                )
            return task_read, True

        task = await self.get_by_id_for_user(task_id, user_id)
        task_read = TaskRead.model_validate(task)
        await cache.set(cache_key, task_read.model_dump(mode="json"))
        return task_read, False

    async def get_all(self) -> list[Task]:
        result = await self.db.execute(select(Task))
        return list(result.scalars().all())

    async def update(
        self,
        task_id: int,
        data: TaskUpdate,
        user_id: int | None = None,
    ) -> Task:
        task = (
            await self.get_by_id_for_user(task_id, user_id)
            if user_id is not None
            else await self.get_by_id(task_id)
        )
        update_data = data.model_dump(exclude_unset=True)

        for field, value in update_data.items():
            if field in {"title", "status"} and value is None:
                raise AppError(
                    code="INVALID_FIELD_VALUE",
                    message=f"{field} cannot be None",
                    status_code=400,
                )
            setattr(task, field, value)

        await self.db.commit()
        await self.db.refresh(task)
        await invalidate_user_task_cache(task.owner_id, task_id=task.id)
        return task

    async def delete(self, task_id: int, user_id: int | None = None) -> Task:
        task = (
            await self.get_by_id_for_user(task_id, user_id)
            if user_id is not None
            else await self.get_by_id(task_id)
        )
        owner_id = task.owner_id
        await self.db.delete(task)
        await self.db.commit()
        await invalidate_user_task_cache(owner_id, task_id=task_id)
        return task

    async def get_user_tasks(self, user_id: int) -> list[Task]:
        results = await self.db.execute(
            select(Task).where(Task.owner_id == user_id)
        )
        return list(results.scalars().all())

    async def get_user_tasks_paginated(
        self,
        user_id: int,
        page: int = 1,
        page_size: int = 20,
        task_status: TaskStatus | None = None,
        q: str | None = None,
        sort_by: Literal["created_at", "due_at", "title", "status"] = "created_at",
        sort_order: Literal["asc", "desc"] = "desc",
    ) -> tuple[PaginatedResponse[TaskRead], bool]:
        status_key = task_status.value if task_status is not None else "all"
        q_key = q.casefold() if q is not None else ""
        cache_key = (
            f"{user_tasks_cache_prefix(user_id)}"
            f"p={page}:s={page_size}:st={status_key}:q={q_key}:sb={sort_by}:so={sort_order}"
        )

        cached = await cache.get(cache_key)
        if cached is not None:
            return PaginatedResponse[TaskRead].model_validate(cached), True

        filters = [Task.owner_id == user_id]
        if task_status is not None:
            filters.append(Task.status == task_status)
        if q is not None:
            pattern = f"%{q.strip()}%"
            filters.append(
                or_(
                    Task.title.ilike(pattern),
                    Task.description.ilike(pattern),
                )
            )

        count_stmt = select(func.count(Task.id)).where(*filters)
        total = (await self.db.execute(count_stmt)).scalar_one()

        sort_column = SORT_COLUMNS[sort_by]
        order_expr = sort_column.asc() if sort_order == "asc" else sort_column.desc()

        offset = (page - 1) * page_size
        query_stmt = (
            select(Task)
            .where(*filters)
            .order_by(order_expr, Task.id.desc())
            .offset(offset)
            .limit(page_size)
        )
        rows = (await self.db.execute(query_stmt)).scalars().all()
        items = [TaskRead.model_validate(task) for task in rows]

        response = PaginatedResponse[TaskRead].create(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
        )
        await cache.set(cache_key, response.model_dump(mode="json"))
        return response, False

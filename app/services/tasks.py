from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.errors import AppError
from app.db.models import Task
from app.schemas.task import TaskCreate, TaskUpdate

class TaskService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, data: TaskCreate) -> Task:
        task = Task(**data.model_dump())
        self.db.add(task)
        await self.db.commit()
        await self.db.refresh(task)
        return task

    async def get_by_id(self, task_id: int) -> Task:
        task = await self.db.get(Task, task_id)
        if task is None:
            raise AppError(status_code=404, detail="Task not found")
        return task

    async def get_all(self) -> list[Task]:
        result = await self.db.execute(select(Task))
        return list(result.scalars().all())

    async def update(self, task_id: int, data: TaskUpdate) -> Task:
        task = await self.get_by_id(task_id)
        update_data = data.model_dump(exclude_unset=True)

        for field, value in update_data.items():
            if field in {"title", "status" } and value is None:
                raise AppError(status_code=400, detail=f"{field} cannot be None")
            setattr(task, field, value)
        await self.db.commit()
        await self.db.refresh(task)
        return task

    async def delete(self, task_id: int) -> None:
        task = await self.get_by_id(task_id)
        await self.db.delete(task)
        await self.db.commit()

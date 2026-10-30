from datetime import datetime, UTC
from app.schemas.task import TaskCreate, TaskStatus, TaskRead, TaskUpdate
from app.core.errors import AppError

class TaskService:
    def __init__(self):
        self.tasks: list[TaskRead] = [
            TaskRead(
                id=1,
                title="Learn FastAPI",
                description="Learn how to build APIs with FastAPI",
                status=TaskStatus.in_progress,
                due_at=None,
                created_at=datetime(2026,10,20, tzinfo=UTC),
            ),

            TaskRead(
                id=2,
                title="Build The Taskflow API",
                description="Implement the first endpoint",
                status=TaskStatus.todo,
                due_at=None,
                created_at=datetime(2026, 10, 21, tzinfo=UTC)
            ),

            TaskRead(
                id=3,
                title="Review HTTP fundamentals",
                description=None,
                status=TaskStatus.done,
                due_at=None,
                created_at=datetime(2026, 10, 22, tzinfo=UTC)
            ),

        ]
        self.next_id = 4

    def create(self, data: TaskCreate) -> TaskRead:
        task = TaskRead(
            id=self.next_id,
            created_at=datetime.now(UTC),
            **data.model_dump(),
        )

        self.tasks.append(task)
        self.next_id += 1

        return task

    def get_all(self) -> list[TaskRead]:
        return self.tasks

    def get_by_id(self, task_id: int) -> bool:
        for task in self.tasks:
            if task.id == task_id:
                return task
        return None

    def delete(self, task_id: int) -> bool:
        task = self.get_by_id(task_id)
        if task is None:
            return False
        self.tasks.remove(task)
        return True

    def update(
        self,
        task_id: int,
        data: TaskUpdate
    ) -> TaskRead | None:
        task = self.get_by_id(task_id)
        if task is None:
            return None

        update_data = data.model_dump(exclude_unset=True)
        if "title" in update_data and update_data["title"] is None:
            raise AppError(
                code="INVALID_TASK_TITLE",
                message="Task title cannot be null",
                status_code=400
            )

        updated_task = task.model_copy(update=update_data)
        self.tasks[self.tasks.index(task)] = updated_task

        return updated_task
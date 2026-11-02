from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.services.tasks import TaskService


DatabaseDep = Annotated[
    AsyncSession,
    Depends(get_db)
]


def get_task_service(
    db: DatabaseDep
) -> TaskService:

    return TaskService(db)


TaskServiceDep = Annotated[
    TaskService,
    Depends(get_task_service)
]


def get_resource():
    print("Opening resource")
    resource = {"name": "TaskFlow"}

    try:
        yield resource
    finally:
        print("Closing resource")


ResourceDep = Annotated[
    dict,
    Depends(get_resource)
]
from typing import Annotated
from fastapi import Depends
from app.services.tasks import TaskService

task_service = TaskService()

def get_task_service() -> TaskService:
    return task_service

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
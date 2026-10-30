from fastapi import FastAPI 
from contextlib import asynccontextmanager
from app.api.tasks import router as tasks_router
from app.core.errors import AppError, app_error_handler
from app.dependencies import ResourceDep
from app.core.config import get_settings

settings = get_settings()

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("TaskFlow is Starting...")

    yield

    print("Taskflow is shutting down...")

app = FastAPI(
    title="TaskFlow API",
    description="API for managing tasks in TaskFlow application",
    version="0.1.0",
    lifespan=lifespan
)

app.add_exception_handler(
    AppError,
    app_error_handler
)

app.include_router(tasks_router)

@app.get("/health")
async def health_check():
    return {"status": "ok", "message": "TaskFlow API is running smoothly."}

@app.get("/resource")
async def get_resource_data(
    resource: ResourceDep
):
    return resource
from fastapi import FastAPI 
from contextlib import asynccontextmanager
from app.api.tasks import router as tasks_router
from app.api.auth import router as auth_router
from app.core.errors import AppError, app_error_handler
from app.dependencies import ResourceDep
from app.core.config import get_settings
from app.db.database import(initialize_database, close_database)
from app.core.middleware import security_headers

from fastapi.middleware.cors import CORSMiddleware

settings = get_settings()

@asynccontextmanager
async def lifespan(app: FastAPI):
    await initialize_database()
    print("TaskFlow is Starting...")

    yield

    await close_database()
    print("Taskflow is shutting down...")

app = FastAPI(
    title="TaskFlow API",
    description="API for managing tasks in TaskFlow application",
    version="0.1.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.middleware("http")(security_headers)

app.add_exception_handler(
    AppError,
    app_error_handler
)

app.include_router(tasks_router)
app.include_router(auth_router)

@app.get("/health")
async def health_check():
    return {"status": "ok", "message": "TaskFlow API is running smoothly."}

@app.get("/resource")
async def get_resource_data(
    resource: ResourceDep
):
    return resource
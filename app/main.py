from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.attachments import router as attachments_router
from app.api.auth import router as auth_router
from app.api.jobs import router as jobs_router
from app.api.tasks import router as tasks_router
from app.api.ws import router as ws_router
from app.core.cache import cache
from app.core.config import get_settings
from app.core.errors import AppError, app_error_handler
from app.core.middleware import security_headers
from app.core.websocket import ws_manager
from app.db.database import close_database, initialize_database
from app.dependencies import ResourceDep

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    Path(settings.upload_dir).mkdir(parents=True, exist_ok=True)
    Path(settings.export_dir).mkdir(parents=True, exist_ok=True)
    await initialize_database()
    print("TaskFlow is Starting...")

    yield

    await close_database()
    print("Taskflow is shutting down...")


app = FastAPI(
    title=settings.app_name or "TaskFlow API",
    description="API for managing tasks in TaskFlow application",
    version=settings.app_version or "0.3.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.middleware("http")(security_headers)

app.add_exception_handler(AppError, app_error_handler)

app.include_router(auth_router)
app.include_router(tasks_router)
app.include_router(attachments_router)
app.include_router(jobs_router)
app.include_router(ws_router)


@app.get("/health")
async def health_check():
    return {
        "status": "ok",
        "message": "TaskFlow API is running smoothly.",
        "cache": await cache.stats(),
        "websocket_connections": await ws_manager.active_connection_count(),
    }


@app.get("/resource")
async def get_resource_data(resource: ResourceDep):
    return resource

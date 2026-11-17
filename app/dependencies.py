from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
import jwt
from jwt.exceptions import InvalidTokenError
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.services.attachments import AttachmentService
from app.services.jobs import JobService
from app.services.tasks import TaskService
from app.services.users import UserService

from app.core.config import get_settings
from app.db.models import User

settings = get_settings()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

DatabaseDep = Annotated[
    AsyncSession,
    Depends(get_db)
]


def get_user_service(
    db: DatabaseDep
) -> UserService:

    return UserService(db)

UserServiceDep = Annotated[
    UserService,
    Depends(get_user_service)
]


async def get_user_from_token(
    token: str,
    service: UserService,
) -> User | None:
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret,
            algorithms=[settings.jwt_algorithm],
        )
        user_id = payload.get("sub")
        if user_id is None:
            return None
        return await service.get_by_id(int(user_id))
    except (InvalidTokenError, ValueError):
        return None


async def get_current_user(
    token: Annotated[
        str,
        Depends(oauth2_scheme)
    ],
    service: UserServiceDep,
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={
            "WWW-Authenticate": "Bearer"
        }
    )

    user = await get_user_from_token(token, service)
    if user is None:
        raise credentials_exception

    return user


CurrentUser = Annotated[
    User,
    Depends(get_current_user)
]

def require_role(required_role: str):
    async def role_checker(current_user: CurrentUser) -> User:
        if current_user.role != required_role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to access this resource",
            )
        return current_user
    return role_checker

def get_task_service(
    db: DatabaseDep
) -> TaskService:

    return TaskService(db)


TaskServiceDep = Annotated[
    TaskService,
    Depends(get_task_service)
]


def get_attachment_service(db: DatabaseDep) -> AttachmentService:
    return AttachmentService(db)


AttachmentServiceDep = Annotated[
    AttachmentService,
    Depends(get_attachment_service),
]


def get_job_service(db: DatabaseDep) -> JobService:
    return JobService(db)


JobServiceDep = Annotated[
    JobService,
    Depends(get_job_service),
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
from typing_extensions import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from app.core.rate_limit import rate_limit
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_access_token,
    verify_password,
)
from app.db.models import User
from app.dependencies import CurrentUser, UserServiceDep, require_role
from app.schemas.auth import RefreshTokenRequest, Token
from app.schemas.user import UserCreate, UserRead

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
)


@router.post(
    "/register",
    response_model=UserRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[rate_limit(max_requests=20, window_seconds=60)],
)
async def register(data: UserCreate, service: UserServiceDep):
    return await service.register(data)


@router.post(
    "/login",
    response_model=Token,
    dependencies=[rate_limit(max_requests=20, window_seconds=60)],
)
async def login(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    service: UserServiceDep,
):
    user = await service.get_by_username(form_data.username)
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(user_id=user.id, role=user.role)
    refresh_token = create_refresh_token(user_id=user.id, role=user.role)
    return Token(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
    )


@router.post(
    "/refresh",
    response_model=Token,
    dependencies=[rate_limit(max_requests=20, window_seconds=60)],
)
async def refresh_tokens(
    body: RefreshTokenRequest,
    service: UserServiceDep,
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired refresh token",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = decode_access_token(body.refresh_token)
    except ValueError:
        raise credentials_exception

    if payload.get("type") != "refresh" or not payload.get("sub"):
        raise credentials_exception

    user = await service.get_by_id(int(payload["sub"]))
    if user is None:
        raise credentials_exception

    return Token(
        access_token=create_access_token(user_id=user.id, role=user.role),
        refresh_token=create_refresh_token(user_id=user.id, role=user.role),
        token_type="bearer",
    )


@router.get("/me", response_model=UserRead)
async def get_me(current_user: CurrentUser):
    return current_user


@router.get("/admin-only")
async def admin_only(
    admin: Annotated[
        User,
        Depends(require_role("admin")),
    ]
):
    return {"message": f"Hello, {admin.username}. You have admin access."}

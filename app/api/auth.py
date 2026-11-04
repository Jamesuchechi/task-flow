from typing_extensions import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from app.db.models import User
from app.dependencies import UserServiceDep, CurrentUser, require_role
from app.schemas.user import UserCreate, UserRead
from app.core.security import create_access_token, verify_password
from app.schemas.auth import Token


router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
)

@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def register(data: UserCreate, service: UserServiceDep):
    user = await service.register(data)
    if not user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User already exists")
    return user

@router.post("/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends(), service: UserServiceDep = None,):
    user = await service.get_by_username(form_data.username)
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(user_id=user.id, role=user.role)
    return Token(access_token=access_token, token_type="bearer")

@router.get("/me", response_model=UserRead)
async def get_me(current_user: CurrentUser):
    return current_user

@router.get("/admin-only")
async def admin_only(admin: Annotated[
    User,
    Depends(require_role("admin")),
]):
    return {"message": f"Hello, {admin.username}. You have admin access."}
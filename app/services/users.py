from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import AppError
from app.core.security import hash_password
from app.db.models import User
from app.schemas.user import UserCreate


class UserService:

    def __init__(self, db: AsyncSession):
        self.db = db

    async def register(
        self,
        data: UserCreate
    ) -> User:

        existing_user = await self.db.execute(
            select(User).where(
                User.username == data.username
            )
        )

        if existing_user.scalar_one_or_none():
            raise AppError(
                code="USERNAME_UNAVAILABLE",
                message="Unable to register with these details",
                status_code=409
            )

        existing_email = await self.db.execute(
            select(User).where(
                User.email == data.email
            )
        )

        if existing_email.scalar_one_or_none():
            raise AppError(
                code="EMAIL_UNAVAILABLE",
                message="Unable to register with these details",
                status_code=409
            )

        user = User(
            username=data.username,
            email=data.email,
            hashed_password=hash_password(data.password),
        )

        self.db.add(user)

        await self.db.commit()
        await self.db.refresh(user)

        return user

    async def get_by_username(
        self,
        username: str
    ) -> User | None:

        result = await self.db.execute(
            select(User).where(
                User.username == username
            )
        )

        return result.scalar_one_or_none()

    async def get_by_id(
        self,
        user_id: int
    ) -> User | None:

        return await self.db.get(User, user_id)
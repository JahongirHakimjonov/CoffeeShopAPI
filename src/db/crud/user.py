from datetime import UTC, datetime, timedelta

from fastapi import Depends
from loguru import logger
from pydantic import EmailStr
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import func

from core.exceptions.user import UserAlreadyRegistered, UserNotFound
from db.dependencies import get_db_session
from db.models.user import User
from schemas.user import UserRegisterSchema, UserUpdateSchema
from services.confirm import ConfirmService


class UserCRUD:
    def __init__(self, session: AsyncSession, confirm_service: ConfirmService):
        self.session = session
        self.confirm_service = confirm_service

    async def get_by_email(self, email: EmailStr) -> User:
        result = await self.session.execute(select(User).where(User.email == email))
        user = result.scalars().first()
        if user is None:
            raise UserNotFound()
        return user

    async def get_by_id(self, user_id: int) -> User:
        result = await self.session.execute(select(User).where(User.id == user_id))
        user = result.scalars().first()
        if user is None:
            raise UserNotFound()
        return user

    async def registration(self, data: UserRegisterSchema) -> User:
        # Проверка, существует ли email
        try:
            await self.get_by_email(data.email)
            raise UserAlreadyRegistered()
        except UserNotFound:
            pass

        user = User(
            email=data.email,
            first_name=data.first_name,
            last_name=data.last_name,
        )
        await user.set_password(data.password)
        self.session.add(user)
        await self.session.commit()
        await self.session.refresh(user)

        # Отправка письма подтверждения
        await self.confirm_service.send_confirm(email=user.email)

        return user

    async def confirm(self, email: EmailStr, code: int) -> bool:
        user = await self.get_by_email(email)
        if user.is_verified:
            return True

        is_confirmed = await self.confirm_service.check_confirm(email=email, code=code)
        if is_confirmed:
            user.is_verified = True
            self.session.add(user)
            await self.session.commit()
            await self.session.refresh(user)
            return True
        return False

    async def resend_confirmation(self, email: EmailStr) -> None:
        user = await self.get_by_email(email)
        if not user or user.is_verified:
            return
        await self.confirm_service.send_confirm(email=email)

    async def get_list(self, limit: int = 100, offset: int = 0) -> tuple[list[User], int]:
        total_stmt = select(func.count()).select_from(User)
        total_result = await self.session.execute(total_stmt)
        total = total_result.scalar_one()

        stmt = select(User).limit(limit).offset(offset)
        result = await self.session.execute(stmt)
        items = list(result.scalars().all())

        return items, total

    async def update(self, user_id: int, data: UserUpdateSchema) -> User:
        user = await self.get_by_id(user_id)
        for key, value in data.model_dump(exclude_unset=True, exclude_none=True).items():
            setattr(user, key, value)
        await self.session.commit()
        await self.session.refresh(user)
        return user

    async def delete(self, user_id: int) -> None:
        user = await self.get_by_id(user_id)
        if user:
            await self.session.delete(user)
            await self.session.commit()

    async def delete_old_unverified_users(self) -> None:
        """
        Delete users who are unverified and older than 2-days.
        """
        threshold = (datetime.now(UTC) - timedelta(days=2)).replace(tzinfo=None)

        stmt = delete(User).where(User.created_at < threshold, User.is_verified.is_(False)).returning(User.id)

        result = await self.session.execute(stmt)
        deleted_ids = result.scalars().all()

        if deleted_ids:
            logger.info(f"Deleted {len(deleted_ids)} old unverified users: {deleted_ids}")
        else:
            logger.info("No old unverified users found.")

        await self.session.commit()


def get_user_crud(
    session: AsyncSession = Depends(get_db_session),
    confirm_service: ConfirmService = Depends(),
) -> UserCRUD:
    return UserCRUD(session=session, confirm_service=confirm_service)

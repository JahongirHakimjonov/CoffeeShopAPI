from datetime import UTC, datetime, timedelta

from pydantic import EmailStr
from sqlalchemy import BigInteger, DateTime, Integer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql.sqltypes import String

from db.base import AbstractBase
from db.models.base import BaseMixin


class ConfirmCode(AbstractBase, BaseMixin):
    __tablename__ = "confirm_code"

    SMS_EXPIRY_SECONDS = 120
    RESEND_BLOCK_MINUTES = 10
    TRY_BLOCK_MINUTES = 2
    RESEND_COUNT = 5
    TRY_COUNT = 10

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    code: Mapped[int] = mapped_column(Integer, index=True, nullable=False)
    try_count: Mapped[int] = mapped_column(Integer, default=0, index=True, nullable=False)
    resend_count: Mapped[int] = mapped_column(Integer, default=0, index=True, nullable=False)
    email: Mapped[EmailStr] = mapped_column(String(255), index=True, nullable=False)

    expire_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
    unlock_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
    resend_unlock_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, index=True)

    async def sync_limits(self, session: AsyncSession) -> None:
        now = datetime.now(UTC)

        if self.resend_count >= self.RESEND_COUNT:
            self.try_count = 0
            self.resend_count = 0
            self.resend_unlock_time = now + timedelta(minutes=self.RESEND_BLOCK_MINUTES)

        elif self.try_count >= self.TRY_COUNT:
            self.try_count = 0
            self.unlock_time = now + timedelta(minutes=self.TRY_BLOCK_MINUTES)

        if self.resend_unlock_time is not None and self.resend_unlock_time < now:
            self.resend_unlock_time = None

        if self.unlock_time is not None and self.unlock_time < now:
            self.unlock_time = None

        await session.commit()

    async def is_expired(self) -> bool | None:
        if self.expire_time is None:
            return None
        return self.expire_time < datetime.now(UTC)

    async def is_block(self) -> bool:
        return self.unlock_time is not None

    async def reset_limits(self) -> None:
        self.try_count = 0
        self.resend_count = 0
        self.unlock_time = None

    async def interval(self, time: datetime) -> str:
        diff = time - datetime.now(UTC)
        total_seconds = max(int(diff.total_seconds()), 0)

        minutes = total_seconds // 60
        seconds = total_seconds % 60
        return f"{minutes:02d}:{seconds:02d}"

    def __repr__(self) -> str:
        return f"<SmsConfirm email={self.email}, code={self.code}>"

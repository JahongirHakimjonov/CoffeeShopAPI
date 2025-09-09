from datetime import UTC, datetime, timedelta

from fastapi import Depends
from pydantic import EmailStr
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.exceptions.confirm import ConfirmError
from db.dependencies import get_db_session
from db.models.confirm import ConfirmCode


class ConfirmCodeCRUD:
    def __init__(self, session: AsyncSession = Depends(get_db_session)):
        self.session = session

    async def get_or_create(self, email: EmailStr, code: int) -> ConfirmCode:
        result = await self.session.execute(select(ConfirmCode).where(ConfirmCode.email == email))
        sms_confirm: ConfirmCode | None = result.scalars().first()

        if sms_confirm is None:
            sms_confirm = ConfirmCode(email=email, code=code)
            self.session.add(sms_confirm)
            await self.session.commit()
            await self.session.refresh(sms_confirm)

        return sms_confirm

    # Новое: получить запись по email
    async def get_by_email(self, email: EmailStr) -> ConfirmCode | None:
        result = await self.session.execute(select(ConfirmCode).where(ConfirmCode.email == email))
        return result.scalars().first()

    # Новое: гарантировать наличие записи (создать при отсутствии)
    async def ensure_exists(self, email: EmailStr, code: int) -> ConfirmCode:
        sms_confirm = await self.get_by_email(email)
        if sms_confirm is None:
            sms_confirm = ConfirmCode(email=email, code=code)
            self.session.add(sms_confirm)
            await self.session.commit()
            await self.session.refresh(sms_confirm)
        return sms_confirm

    # Новое: подготовка к отправке кода + сохранение лимитов/счетчиков
    async def prepare_and_save_code(self, email: EmailStr, code: int) -> ConfirmCode:
        sms_confirm = await self.ensure_exists(email, code)

        # Актуализируем лимиты (метод модели)
        await sms_confirm.sync_limits(self.session)

        # Проверка блокировки на повторную отправку
        if sms_confirm.resend_unlock_time is not None:
            expired = await sms_confirm.interval(sms_confirm.resend_unlock_time)
            raise ConfirmError(f"Resend blocked, try again in {expired}", values={"expired": expired})

        # Обновляем поля для нового кода
        sms_confirm.code = code
        sms_confirm.try_count = 0
        sms_confirm.resend_count += 1
        sms_confirm.expire_time = datetime.now(UTC) + timedelta(seconds=ConfirmCode.SMS_EXPIRY_SECONDS)
        sms_confirm.resend_unlock_time = datetime.now(UTC) + timedelta(seconds=ConfirmCode.SMS_EXPIRY_SECONDS)

        self.session.add(sms_confirm)
        await self.session.commit()
        await self.session.refresh(sms_confirm)
        return sms_confirm

    # Новое: проверка кода подтверждения
    async def verify_code(self, email: EmailStr, code: int) -> bool:
        sms_confirm = await self.get_by_email(email)
        if sms_confirm is None:
            raise ConfirmError("Invalid confirmation code")

        await sms_confirm.sync_limits(self.session)

        if await sms_confirm.is_expired():
            raise ConfirmError("Time for confirmation has expired")

        if await sms_confirm.is_block():
            if sms_confirm.unlock_time is not None:
                expired = await sms_confirm.interval(sms_confirm.unlock_time)
                raise ConfirmError(f"Try again in {expired}")
            else:
                raise ConfirmError("Unlock time is not set")

        if sms_confirm.code == code:
            await self.session.delete(sms_confirm)
            await self.session.commit()
            return True

        sms_confirm.try_count += 1
        self.session.add(sms_confirm)
        await self.session.commit()
        raise ConfirmError("Invalid confirmation code")

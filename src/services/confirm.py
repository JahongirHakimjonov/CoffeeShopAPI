# services/confirm.py

import secrets

from fastapi import Depends
from loguru import logger
from pydantic import EmailStr

from core.celery.tasks.confirm import send_confirm_task
from core.exceptions.confirm import ConfirmError
from core.settings import settings
from db.crud.confirm import ConfirmCodeCRUD


class ConfirmService:
    def __init__(self, confirm_crud: ConfirmCodeCRUD = Depends()):
        self.confirm_crud = confirm_crud

    async def send_confirm(self, email: EmailStr) -> bool:
        """
        Generate and send email confirmation code.
        If a ConfirmError occurs (e.g. resend blocked), re-raise it so the API
        layer can return the proper error response to the client.
        """
        code = 1111
        if not settings.debug:
            code = secrets.randbelow(9000) + 1000

        try:
            # prepare_and_save_code may raise ConfirmError -> let it bubble up
            await self.confirm_crud.prepare_and_save_code(email, code)
            # send async with Celery
            send_confirm_task.delay(email, code)
        except ConfirmError:
            # Re-raise so FastAPI (and your APIException handler) returns the ConfirmError response.
            raise
        except Exception as e:
            # Unexpected errors are logged and we return False (so caller can handle generic failure)
            logger.exception(e)
            return False

        return True

    async def check_confirm(self, email: EmailStr, code: int) -> bool:
        """
        Check confirmation code validity.
        """
        try:
            await self.confirm_crud.verify_code(email, code)
            return True
        except ConfirmError:
            raise
        except Exception as e:
            logger.exception(e)
            return False

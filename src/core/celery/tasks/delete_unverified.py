# tasks/user_cleanup.py
import asyncio

from loguru import logger

from core.celery.app import celery_app
from core.database import get_session_factory
from db.crud.user import UserCRUD
from services.confirm import ConfirmService


@celery_app.task(name="cleanup_old_unverified_users")  # type: ignore
def cleanup_old_unverified_users() -> None:
    """
    Celery task: delete unverified users older than 2 days.
    """

    async def _run() -> None:
        session_factory = get_session_factory()
        async with session_factory() as session:
            confirm_service = ConfirmService()
            crud = UserCRUD(session=session, confirm_service=confirm_service)
            await crud.delete_old_unverified_users()

    logger.info("Celery task started: cleanup_old_unverified_users")
    asyncio.run(_run())
    logger.info("Celery task finished: cleanup_old_unverified_users")

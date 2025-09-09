from celery import Celery

from core.settings import redis_settings, settings

celery_app = Celery(
    settings.app_name,
    broker=redis_settings.url,
    backend=redis_settings.url,
    include=[
        "core.celery.tasks.confirm",
        "core.celery.tasks.delete_unverified",
    ],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=60 * 60,  # 30 minutes
    worker_prefetch_multiplier=1,
    task_acks_late=True,
    broker_connection_retry=True,
    beat_schedule={
        "cleanup_old_unverified_users": {
            "task": "cleanup_old_unverified_users",
            "schedule": 60.0,  # every day at midnight
        },
    },
)

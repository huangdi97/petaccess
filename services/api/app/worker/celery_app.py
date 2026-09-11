"""Celery worker app: rule-change watch notifications (design #24, GOAL #16).

Uses the mock notification provider by default; real channel adapters land
with credentials (see BLOCKERS.md).
"""

from celery import Celery

from app.core.config import get_settings

settings = get_settings()

celery_app = Celery(
    "petaccess-worker",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=["app.worker.tasks"],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    beat_schedule={
        # hourly sweep for due rule-change notifications
        "watch-notify-sweep": {"task": "app.worker.tasks.notify_rule_changes", "schedule": 3600.0},
    },
)


@celery_app.task(name="app.worker.tasks.healthcheck_task")
def healthcheck_task() -> dict:
    return {"status": "worker_alive"}

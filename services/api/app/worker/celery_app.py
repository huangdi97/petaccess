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
    # bounded redelivery: visibility_timeout guards against lost workers
    broker_transport_options={"visibility_timeout": 3600},
    beat_schedule={
        # hourly sweep for due rule-change notifications
        "watch-notify-sweep": {"task": "app.worker.tasks.notify_rule_changes", "schedule": 3600.0},
        # hourly TTL purge for expired media (design #20/#28)
        "media-ttl-sweep": {
            "task": "app.worker.tasks.cleanup_expired_scene_photos",
            "schedule": 3600.0,
        },
    },
)


from celery.signals import task_failure  # noqa: E402

from app.core.observability import metrics, record_failed_job  # noqa: E402


@task_failure.connect
def _on_task_failure(sender=None, task_id=None, exception=None, **kwargs):
    """Failed-job visibility: Redis list + metrics counter (NEXT_GOAL §A5)."""
    name = getattr(sender, "name", "unknown")
    record_failed_job(name, task_id or "", str(exception) if exception else "unknown")
    metrics.incr("worker.task_failures")


@celery_app.task(name="app.worker.tasks.healthcheck_task")
def healthcheck_task() -> dict:
    return {"status": "worker_alive"}

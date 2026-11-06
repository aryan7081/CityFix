import logging

from celery import shared_task
from django.core.cache import cache
from django.db import OperationalError

logger = logging.getLogger("cityfix")


@shared_task(
    bind=True,
    autoretry_for=(OperationalError, ConnectionError, TimeoutError),
    retry_backoff=True,
    retry_kwargs={"max_retries": 5},
    name="notifications.enqueue_notification",
)
def enqueue_notification(
    self,
    recipient_id: int,
    kind: str,
    title: str,
    message: str,
    issue_id: int | None = None,
):
    """Create an in-app notification asynchronously via Celery + Redis broker."""
    from notifications.models import Notification

    notification = Notification.objects.create(
        recipient_id=recipient_id,
        kind=kind,
        title=title,
        message=message,
        issue_id=issue_id,
    )
    try:
        cache.incr("metrics:celery_tasks_processed")
    except Exception:
        try:
            cache.add("metrics:celery_tasks_processed", 1)
        except Exception:
            logger.debug("Could not increment celery metrics counter")

    logger.info(
        "Notification created id=%s kind=%s recipient=%s",
        notification.id,
        kind,
        recipient_id,
    )
    return notification.id


@shared_task(bind=True, name="notifications.ping")
def ping(self):
    try:
        cache.incr("metrics:celery_tasks_processed")
    except Exception:
        cache.add("metrics:celery_tasks_processed", 1)
    return "pong"

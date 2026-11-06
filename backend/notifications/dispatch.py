"""Safe notification dispatch — never fail the HTTP request if the broker is down."""

from __future__ import annotations

import logging

logger = logging.getLogger("cityfix")


def dispatch_notification(
    *,
    recipient_id: int,
    kind: str,
    title: str,
    message: str,
    issue_id: int | None = None,
) -> None:
    from notifications.tasks import enqueue_notification

    try:
        enqueue_notification.delay(
            recipient_id=recipient_id,
            kind=kind,
            title=title,
            message=message,
            issue_id=issue_id,
        )
    except Exception as exc:
        logger.warning(
            "Celery dispatch failed (%s); creating notification synchronously",
            exc,
        )
        try:
            enqueue_notification(
                recipient_id=recipient_id,
                kind=kind,
                title=title,
                message=message,
                issue_id=issue_id,
            )
        except Exception:
            logger.exception("Synchronous notification fallback also failed")

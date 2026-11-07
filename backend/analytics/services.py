from __future__ import annotations

from datetime import timedelta

from django.db.models import Avg, Count, DurationField, ExpressionWrapper, F, Q
from django.db.models.functions import TruncDate
from django.utils import timezone

from issues.models import Issue, IssueDuplicate
from .cache_metrics import DASHBOARD_STATS_KEY, PUBLIC_STATS_KEY, get_or_set


def _compute_dashboard_stats() -> dict:
    now = timezone.now()
    qs = Issue.objects.all()
    resolved = qs.filter(status=Issue.Status.RESOLVED, resolved_at__isnull=False)

    avg_resolution = resolved.annotate(
        duration=ExpressionWrapper(
            F("resolved_at") - F("created_at"),
            output_field=DurationField(),
        )
    ).aggregate(avg=Avg("duration"))["avg"]

    avg_hours = None
    if avg_resolution is not None:
        avg_hours = round(avg_resolution.total_seconds() / 3600, 2)

    by_category = list(
        qs.values("category").annotate(count=Count("id")).order_by("-count")
    )
    by_status = list(qs.values("status").annotate(count=Count("id")).order_by("-count"))
    by_priority = list(
        qs.values("priority").annotate(count=Count("id")).order_by("-count")
    )

    last_14 = now - timedelta(days=14)
    over_time = list(
        qs.filter(created_at__gte=last_14)
        .annotate(day=TruncDate("created_at"))
        .values("day")
        .annotate(count=Count("id"))
        .order_by("day")
    )
    for row in over_time:
        row["day"] = row["day"].isoformat() if row["day"] else None

    total = qs.count()
    resolved_count = qs.filter(status=Issue.Status.RESOLVED).count()
    resolution_rate = round((resolved_count / total) * 100, 1) if total else 0.0

    return {
        "total_issues": total,
        "pending_verification": qs.filter(
            status__in=[Issue.Status.REPORTED, Issue.Status.UNDER_REVIEW]
        ).count(),
        "high_priority_open": qs.filter(
            priority__in=[Issue.Priority.HIGH, Issue.Priority.CRITICAL]
        )
        .exclude(status__in=[Issue.Status.RESOLVED, Issue.Status.REJECTED])
        .count(),
        "resolved_issues": resolved_count,
        "resolution_rate_percent": resolution_rate,
        "average_resolution_hours": avg_hours,
        "by_category": by_category,
        "by_status": by_status,
        "by_priority": by_priority,
        "reported_over_time": over_time,
        "duplicate_candidates_detected": IssueDuplicate.objects.count(),
        "generated_at": now.isoformat(),
        "cache_source": "computed",
    }


def get_dashboard_stats(*, use_cache: bool = True) -> dict:
    if not use_cache:
        # Force a fresh compute and rewrite the cache entry (evaluation-friendly).
        from .cache_metrics import invalidate_dashboard_caches

        invalidate_dashboard_caches()

    data = get_or_set(DASHBOARD_STATS_KEY, _compute_dashboard_stats)
    result = dict(data)
    result["cache_source"] = "redis"
    return result


def get_public_stats() -> dict:
    def producer():
        qs = Issue.objects.all()
        return {
            "total_issues": qs.count(),
            "resolved_issues": qs.filter(status=Issue.Status.RESOLVED).count(),
            "open_issues": qs.exclude(
                status__in=[Issue.Status.RESOLVED, Issue.Status.REJECTED]
            ).count(),
            "generated_at": timezone.now().isoformat(),
        }

    return get_or_set(PUBLIC_STATS_KEY, producer)

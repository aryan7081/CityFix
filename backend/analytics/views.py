import logging

from django.db import connection
from django.core.cache import cache
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from common.permissions import IsAdminRole
from issues.models import IssueDuplicate

from .cache_metrics import get_cache_counters, invalidate_dashboard_caches
from .services import get_dashboard_stats, get_public_stats

logger = logging.getLogger("cityfix")


class DashboardStatsView(APIView):
    permission_classes = [IsAdminRole]

    def get(self, request):
        bypass = request.query_params.get("bypass_cache") == "1"
        data = get_dashboard_stats(use_cache=not bypass)
        counters = get_cache_counters()
        data["cache_counters"] = counters
        return Response(data)


class PublicStatsView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        return Response(get_public_stats())


class InvalidateCacheView(APIView):
    permission_classes = [IsAdminRole]

    def post(self, request):
        invalidate_dashboard_caches()
        return Response({"success": True, "message": "Dashboard caches invalidated."})


class SystemHealthView(APIView):
    """
    Architecture evaluation endpoint — real runtime metrics where possible.
    Distinguishes live probes from illustrative fields.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        # Database probe
        db_ok = False
        db_latency_ms = None
        try:
            import time

            start = time.perf_counter()
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                cursor.fetchone()
            db_ok = True
            db_latency_ms = round((time.perf_counter() - start) * 1000, 2)
        except Exception as exc:
            logger.warning("DB health check failed: %s", exc)

        # Redis probe
        redis_ok = False
        try:
            cache.set("health:ping", "pong", timeout=10)
            redis_ok = cache.get("health:ping") == "pong"
        except Exception as exc:
            logger.warning("Redis health check failed: %s", exc)

        # Celery broker probe (best-effort)
        celery_ok = False
        pending_tasks = None
        try:
            from config.celery import app as celery_app

            inspector = celery_app.control.inspect(timeout=1.0)
            ping = inspector.ping() if inspector else None
            celery_ok = bool(ping)
            reserved = inspector.reserved() if inspector else None
            active = inspector.active() if inspector else None
            if reserved is not None and active is not None:
                pending_tasks = sum(len(v) for v in reserved.values()) + sum(
                    len(v) for v in active.values()
                )
        except Exception as exc:
            logger.warning("Celery health check failed: %s", exc)

        counters = get_cache_counters()
        samples = counters.get("api_response_times_ms") or []
        avg_api = round(sum(samples) / len(samples), 2) if samples else None

        return Response(
            {
                "components": {
                    "database": {
                        "status": "up" if db_ok else "down",
                        "latency_ms": db_latency_ms,
                        "metric_type": "real",
                    },
                    "redis": {
                        "status": "up" if redis_ok else "down",
                        "metric_type": "real",
                    },
                    "celery": {
                        "status": "up" if celery_ok else "down_or_unreachable",
                        "pending_or_active_tasks": pending_tasks,
                        "metric_type": "real" if celery_ok else "best_effort",
                        "note": (
                            "Worker ping via Celery inspect; may be unavailable "
                            "if no workers are running."
                        ),
                    },
                },
                "cache": {
                    **counters,
                    "metric_type": "real",
                    "note": "Counters live in Redis; reset when Redis is flushed.",
                },
                "api": {
                    "average_response_ms": avg_api,
                    "recent_samples_ms": samples[-10:],
                    "metric_type": "real",
                },
                "duplicates": {
                    "detected_total": IssueDuplicate.objects.count(),
                    "metric_type": "real",
                },
                "query_example": {
                    "description": "Indexed filter: open HIGH/CRITICAL issues",
                    "sql_hint": "Uses issue_status_priority_idx",
                    "count": self._high_priority_open_count(),
                    "metric_type": "real",
                },
            }
        )

    def _high_priority_open_count(self):
        from issues.models import Issue

        return (
            Issue.objects.filter(priority__in=["HIGH", "CRITICAL"])
            .exclude(status__in=["RESOLVED", "REJECTED"])
            .count()
        )

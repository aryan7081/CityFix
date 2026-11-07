"""
Redis caching helpers with explicit hit/miss logging for evaluation demos.
"""

from __future__ import annotations

import logging
from typing import Any, Callable

from django.core.cache import cache

logger = logging.getLogger("cityfix.cache")

DASHBOARD_STATS_KEY = "analytics:dashboard_stats"
PUBLIC_STATS_KEY = "analytics:public_stats"
CACHE_TTL_SECONDS = 60


def _bump(key: str) -> None:
    try:
        cache.incr(key)
    except Exception:
        try:
            cache.add(key, 1)
        except Exception:
            logger.debug("Unable to bump metric %s", key)


def record_hit(key: str) -> None:
    _bump("metrics:cache_hits")
    logger.info("CACHE HIT key=%s", key)


def record_miss(key: str) -> None:
    _bump("metrics:cache_misses")
    logger.info("CACHE MISS key=%s", key)


def get_or_set(key: str, producer: Callable[[], Any], ttl: int = CACHE_TTL_SECONDS) -> Any:
    try:
        value = cache.get(key)
    except Exception as exc:
        logger.warning("Redis unavailable on GET (%s); computing without cache", exc)
        return producer()

    if value is not None:
        record_hit(key)
        return value

    record_miss(key)
    value = producer()
    try:
        cache.set(key, value, timeout=ttl)
    except Exception as exc:
        logger.warning("Redis unavailable on SET (%s); returning uncached value", exc)
    return value


def invalidate_dashboard_caches() -> None:
    keys = [DASHBOARD_STATS_KEY, PUBLIC_STATS_KEY]
    try:
        cache.delete_many(keys)
        logger.info("CACHE INVALIDATE keys=%s", keys)
        _bump("metrics:cache_invalidations")
    except Exception as exc:
        logger.warning("Cache invalidation failed: %s", exc)


def get_cache_counters() -> dict:
    return {
        "hits": cache.get("metrics:cache_hits") or 0,
        "misses": cache.get("metrics:cache_misses") or 0,
        "invalidations": cache.get("metrics:cache_invalidations") or 0,
        "celery_tasks_processed": cache.get("metrics:celery_tasks_processed") or 0,
        "api_request_count": cache.get("metrics:api_request_count") or 0,
        "api_response_times_ms": cache.get("metrics:api_response_times") or [],
    }

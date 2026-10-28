import logging
import time

from django.core.cache import cache

logger = logging.getLogger("cityfix")


class RequestTimingMiddleware:
    """Records recent API response times for the system-health dashboard."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        start = time.perf_counter()
        response = self.get_response(request)
        elapsed_ms = (time.perf_counter() - start) * 1000
        response["X-Response-Time-Ms"] = f"{elapsed_ms:.2f}"

        if request.path.startswith("/api/"):
            try:
                samples = cache.get("metrics:api_response_times", [])
                samples = (samples + [round(elapsed_ms, 2)])[-50:]
                cache.set("metrics:api_response_times", samples, timeout=3600)
                cache.incr("metrics:api_request_count")
            except Exception:
                # Cache may be unavailable — never break the request.
                try:
                    cache.add("metrics:api_request_count", 1)
                except Exception:
                    logger.debug("Could not record API timing metrics")

        return response

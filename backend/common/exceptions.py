import logging

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import exception_handler

logger = logging.getLogger("cityfix")


def cityfix_exception_handler(exc, context):
    response = exception_handler(exc, context)
    if response is not None:
        payload = {
            "success": False,
            "error": {
                "status_code": response.status_code,
                "detail": response.data,
            },
        }
        response.data = payload
        return response

    logger.exception("Unhandled exception in %s", context.get("view"))
    return Response(
        {
            "success": False,
            "error": {
                "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "detail": "An unexpected server error occurred.",
            },
        },
        status=status.HTTP_500_INTERNAL_SERVER_ERROR,
    )

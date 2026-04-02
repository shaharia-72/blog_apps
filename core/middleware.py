"""
core/middleware.py
==================
FIXED: __init__ typo (was __int__).
ADDED: SecurityHeadersMiddleware referenced in settings.
"""

import time
import logging

logger = logging.getLogger(__name__)


class RequestTimingMiddleware:
    """Log slow requests and add X-Response-Time header."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        start = time.perf_counter()
        response = self.get_response(request)
        duration = time.perf_counter() - start

        if duration > 1.0:
            logger.warning(
                "SLOW REQUEST: %s %s → %dms (status=%d)",
                request.method,
                request.path,
                int(duration * 1000),
                response.status_code,
            )
        response["X-Response-Time"] = f"{duration * 1000:.1f}ms"
        return response


class SecurityHeadersMiddleware:
    """
    Add security headers to every response.
    Supplements Django's built-in security headers.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        response["X-Content-Type-Options"] = "nosniff"
        response["X-Frame-Options"] = "DENY"
        response["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
        return response


class RatelimitMiddleware:
    """
    Catch Ratelimited exception from django-ratelimit and return JSON 429.
    Required for professional REST API responses.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        return self.get_response(request)

    def process_exception(self, request, exception):
        from django_ratelimit.exceptions import Ratelimited
        from django.http import JsonResponse

        if isinstance(exception, Ratelimited):
            return JsonResponse(
                {"error": "Too many requests. Please slow down and try again later. 🛑"},
                status=429,
            )
        return None

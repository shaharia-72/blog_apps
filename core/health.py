"""
core/health.py
===============
Health check endpoint for monitoring, Docker healthcheck, and load balancers.
GET /api/v1/health/ → { "status": "healthy", ... }
"""

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django.core.cache import cache
from django.db import connection
from django.conf import settings
import time


class HealthCheckView(APIView):
    """
    GET /api/v1/health/

    Checks:
      1. Django is running
      2. Database is reachable
      3. Redis cache is reachable

    Used by:
      - Docker HEALTHCHECK
      - Uptime monitoring (UptimeRobot, Pingdom)
      - Load balancer health probes
    """

    permission_classes = [AllowAny]
    authentication_classes = []  # Skip auth overhead

    def get(self, request):
        checks = {}
        healthy = True

        # Check database
        try:
            start = time.perf_counter()
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
            checks["database"] = {
                "status": "up",
                "response_ms": round((time.perf_counter() - start) * 1000, 1),
            }
        except Exception as e:
            checks["database"] = {"status": "down", "error": str(e)}
            healthy = False

        # Check Redis cache
        try:
            start = time.perf_counter()
            cache.set("health_check", "ok", 10)
            val = cache.get("health_check")
            checks["cache"] = {
                "status": "up" if val == "ok" else "degraded",
                "response_ms": round((time.perf_counter() - start) * 1000, 1),
            }
        except Exception as e:
            checks["cache"] = {"status": "down", "error": str(e)}
            healthy = False

        status_code = 200 if healthy else 503
        return Response(
            {
                "status": "healthy" if healthy else "unhealthy",
                "checks": checks,
                "version": "1.0.0",
            },
            status=status_code,
        )

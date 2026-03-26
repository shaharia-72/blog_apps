"""
apps/analytics/apps.py
"""

from django.apps import AppConfig


class AnalyticsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.analytics'
    verbose_name = 'Analytics & Tracking'

    def ready(self):
        """Import signals when app is ready."""
        # Import signals here if needed
        pass

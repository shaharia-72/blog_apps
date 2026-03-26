"""
apps/blog/apps.py
"""

from django.apps import AppConfig


class BlogConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.blog'
    verbose_name = 'Blog Management'

    def ready(self):
        """Import signals when app is ready."""
        # Import signals here if needed
        pass

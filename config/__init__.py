"""
config/__init__.py
===================
This ensures Celery app is loaded when Django starts.
Without this, @shared_task decorator won't discover tasks.
"""
from .celery import app as celery_app

__all__ = ['celery_app']

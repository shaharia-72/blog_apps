"""
apps/blog/tasks.py

FIX: cache.delete_pattern() is django-redis specific. Added AttributeError
     fallback so the task doesn't crash if a different cache backend is used.
"""

from celery import shared_task
from django.core.cache import cache
from django.db import models
import logging

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def rebuild_sitemap(self):
    """
    Clears cached sitemap so next request regenerates it.
    Runs every 6 hours via celery beat.
    """
    try:
        cache.delete("sitemap:blogs")
        cache.delete("sitemap:categories")
        cache.delete("sitemap:static")
        logger.info("Sitemap cache cleared — will rebuild on next request")
    except Exception as exc:
        raise self.retry(exc=exc, countdown=60 * (2**self.request.retries))


@shared_task(bind=True, max_retries=3)
def rebuild_rss_feed(self):
    """
    Clears RSS feed cache so it's regenerated fresh.
    Runs every 30 minutes via celery beat.
    """
    try:
        # FIX: delete_pattern() is django-redis specific.
        # Wrap in try/except so this task works with any cache backend.
        try:
            cache.delete_pattern("blog:rss:*")
        except AttributeError:
            # Non-redis backend — delete known keys manually
            cache.delete("blog:rss:latest")
            logger.warning("delete_pattern not available; cleared known RSS keys only")
        logger.info("RSS feed cache cleared")
    except Exception as exc:
        raise self.retry(exc=exc, countdown=60)


@shared_task
def sync_view_counts():
    """
    Batch-sync view counters from Redis → PostgreSQL.
    Runs every hour via celery beat.

    Pattern explanation:
      Instead of writing to DB on every page view (10,000 writes/hour),
      we increment a Redis counter (microseconds, no DB hit),
      then once per hour flush all counters to DB in one operation.
      This reduces DB write load by ~99% under high traffic.
    """
    from apps.blog.models import Blog

    blogs = Blog.objects.filter(status="published").only("id", "views")
    synced = 0

    for blog in blogs:
        redis_key = f"blog:views:{blog.id}"
        redis_count = cache.get(redis_key)

        if redis_count:
            Blog.objects.filter(id=blog.id).update(
                views=models.F("views") + int(redis_count)
            )
            cache.delete(redis_key)
            synced += 1

    logger.info(f"Synced view counts for {synced} blogs")

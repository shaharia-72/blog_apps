"""
apps/blog/tasks.py
===================
Celery background tasks for the blog app.
Run automatically by celery beat on schedule.
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
        # Django caches the sitemap response — delete it to force rebuild
        cache.delete("sitemap:blogs")
        cache.delete("sitemap:categories")
        cache.delete("sitemap:static")
        logger.info("Sitemap cache cleared — will rebuild on next request")
    except Exception as exc:
        # Retry with exponential backoff: 1m, 2m, 4m
        raise self.retry(exc=exc, countdown=60 * (2**self.request.retries))


@shared_task(bind=True, max_retries=3)
def rebuild_rss_feed(self):
    """
    Clears RSS feed cache so it's regenerated fresh.
    Runs every 30 minutes via celery beat.
    """
    try:
        cache.delete_pattern("blog:rss:*")
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
            # F() expression = atomic DB increment (no race condition)
            Blog.objects.filter(id=blog.id).update(
                views=models.F("views") + int(redis_count)
            )
            cache.delete(redis_key)
            synced += 1

    logger.info(f"Synced view counts for {synced} blogs")

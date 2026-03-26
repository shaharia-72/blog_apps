"""
apps/analytics/tasks.py
========================
Celery tasks for analytics processing.
"""

from celery import shared_task
from django.db import transaction
from django.db.models import Count
from django.db.models.functions import TruncHour
from django.utils import timezone
from datetime import timedelta
import logging

logger = logging.getLogger(__name__)


@shared_task(
    bind=True,
    max_retries=3,
    queue="analytics",
    acks_late=True,  # Task not acknowledged until it completes (no data loss)
    default_retry_delay=60,
)
def record_blog_view(
    self, blog_id, ip_hash, user_agent, referrer, utm_source, utm_medium, utm_campaign
):
    """
    Write one blog view record to PostgreSQL asynchronously.

    Called from views.py AFTER the API already returned a response
    to the user — so the DB write doesn't add latency to the request.

    Why acks_late=True?
    If the Celery worker crashes mid-task, the task stays in the queue
    and gets retried — no view is lost.
    """
    try:
        from apps.blog.models import Blog
        from .models import BlogView

        blog = Blog.objects.get(id=blog_id)
        BlogView.objects.create(
            blog=blog,
            ip_hash=ip_hash,
            user_agent=user_agent[:255] if user_agent else "",
            referrer=referrer[:500] if referrer else "",
            utm_source=utm_source[:100] if utm_source else "",
            utm_medium=utm_medium[:100] if utm_medium else "",
            utm_campaign=utm_campaign[:100] if utm_campaign else "",
        )
    except Exception as exc:
        logger.error(f"record_blog_view failed for blog {blog_id}: {exc}")
        raise self.retry(exc=exc)


@shared_task(queue="analytics")
def aggregate_hourly_stats():
    """
    Runs every hour via celery beat.
    Reads the last 2 hours of raw BlogView events and
    aggregates them into HourlyBlogStat rows.

    Why 2 hours? In case the previous run was delayed/missed —
    we always overlap to avoid gaps in the stats.

    Pattern: raw events → group by (blog, hour) → upsert summary table.
    """
    from .models import BlogView, HourlyBlogStat

    two_hours_ago = timezone.now() - timedelta(hours=2)

    # Group raw views by (blog, truncated_hour)
    aggregated = (
        BlogView.objects.filter(viewed_at__gte=two_hours_ago)
        .annotate(hour=TruncHour("viewed_at"))
        .values("blog", "hour")
        .annotate(view_count=Count("id"))
    )

    with transaction.atomic():
        for row in aggregated:
            HourlyBlogStat.objects.update_or_create(
                blog_id=row["blog"],
                hour=row["hour"],
                defaults={"view_count": row["view_count"]},
            )

    logger.info(f"Aggregated {len(aggregated)} hourly stat rows")

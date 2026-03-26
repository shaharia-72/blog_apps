"""
apps/analytics/tasks.py
========================
Enhanced Celery tasks for analytics processing.
"""

from celery import shared_task
from django.db import transaction
from django.db.models import Count, Avg, Q
from django.db.models.functions import TruncHour, TruncDate
from django.utils import timezone
from datetime import timedelta, date
import logging

logger = logging.getLogger(__name__)


@shared_task(
    bind=True,
    max_retries=3,
    queue="analytics",
    acks_late=True,
    default_retry_delay=60,
)
def record_blog_view(
    self,
    blog_id,
    ip_hash,
    user_agent,
    referrer,
    utm_source,
    utm_medium,
    utm_campaign,
    country_code='',
    city='',
):
    """
    Record a blog view asynchronously.
    Also updates visitor session tracking.
    """
    try:
        from apps.blog.models import Blog
        from .models import BlogView, VisitorSession

        blog = Blog.objects.get(id=blog_id)

        # Create blog view record
        BlogView.objects.create(
            blog=blog,
            ip_hash=ip_hash,
            user_agent=user_agent[:255] if user_agent else "",
            referrer=referrer[:500] if referrer else "",
            utm_source=utm_source[:100] if utm_source else "",
            utm_medium=utm_medium[:100] if utm_medium else "",
            utm_campaign=utm_campaign[:100] if utm_campaign else "",
            country_code=country_code[:2] if country_code else "",
            city=city[:100] if city else "",
        )

        # Update or create visitor session
        today = timezone.now().date()
        session, created = VisitorSession.objects.get_or_create(
            ip_hash=ip_hash,
            session_date=today,
            defaults={
                'country_code': country_code[:2] if country_code else "",
                'page_views': 1,
            }
        )

        if not created:
            # Update existing session
            session.page_views += 1
            session.last_seen = timezone.now()
            session.save(update_fields=['page_views', 'last_seen'])

        logger.info(f"Recorded view for blog {blog_id} from {ip_hash[:8]}")

    except Exception as exc:
        logger.error(f"record_blog_view failed for blog {blog_id}: {exc}")
        raise self.retry(exc=exc)


@shared_task(queue="analytics")
def aggregate_hourly_stats():
    """
    Aggregate blog views into hourly statistics.
    Runs every hour via celery beat.
    """
    from .models import BlogView, HourlyBlogStat

    # Process last 2 hours (overlap to avoid gaps)
    two_hours_ago = timezone.now() - timedelta(hours=2)

    # Group by blog and hour
    aggregated = (
        BlogView.objects.filter(viewed_at__gte=two_hours_ago)
        .annotate(hour=TruncHour("viewed_at"))
        .values("blog", "hour")
        .annotate(
            view_count=Count("id"),
            unique_visitors=Count("ip_hash", distinct=True),
            avg_time_spent=Avg("time_spent_seconds"),
            avg_scroll_depth=Avg("scroll_depth_percent"),
        )
    )

    with transaction.atomic():
        for row in aggregated:
            # Find most common traffic source for this hour
            top_source_data = (
                BlogView.objects.filter(
                    blog_id=row["blog"],
                    viewed_at__gte=row["hour"],
                    viewed_at__lt=row["hour"] + timedelta(hours=1),
                )
                .values("utm_source")
                .annotate(count=Count("id"))
                .order_by("-count")
                .first()
            )

            top_source = top_source_data["utm_source"] if top_source_data else ""

            HourlyBlogStat.objects.update_or_create(
                blog_id=row["blog"],
                hour=row["hour"],
                defaults={
                    "view_count": row["view_count"],
                    "unique_visitors": row["unique_visitors"],
                    "avg_time_spent": int(row["avg_time_spent"] or 0),
                    "avg_scroll_depth": int(row["avg_scroll_depth"] or 0),
                    "top_source": top_source,
                },
            )

    logger.info(f"Aggregated {len(aggregated)} hourly stat rows")


@shared_task(queue="analytics")
def calculate_trending_posts():
    """
    Calculate trending/popular posts for different timeframes.
    Runs daily via celery beat.
    """
    from .models import BlogView, PopularContent
    from apps.blog.models import Blog

    now = timezone.now()

    timeframes = {
        'today': now - timedelta(days=1),
        'week': now - timedelta(days=7),
        'month': now - timedelta(days=30),
        'all_time': None,  # No time limit
    }

    for timeframe_name, start_date in timeframes.items():
        # Build query
        query = BlogView.objects.all()
        if start_date:
            query = query.filter(viewed_at__gte=start_date)

        # Aggregate by blog
        popular = (
            query
            .values('blog')
            .annotate(
                view_count=Count('id'),
                unique_visitors=Count('ip_hash', distinct=True),
            )
            .order_by('-view_count')
            [:50]  # Top 50
        )

        # Clear old data for this timeframe
        PopularContent.objects.filter(timeframe=timeframe_name).delete()

        # Insert new rankings
        for rank, item in enumerate(popular, start=1):
            PopularContent.objects.create(
                blog_id=item['blog'],
                timeframe=timeframe_name,
                rank=rank,
                view_count=item['view_count'],
                unique_visitors=item['unique_visitors'],
            )

        logger.info(f"Updated {len(popular)} popular posts for {timeframe_name}")


@shared_task(queue="analytics")
def calculate_system_metrics():
    """
    Calculate daily system-wide metrics.
    Runs daily at midnight via celery beat.
    """
    from core.models import SystemMetrics
    from .models import BlogView, VisitorSession
    from apps.blog.models import Blog
    from apps.newsletter.models import Subscriber
    from apps.contact.models import ContactMessage

    yesterday = (timezone.now() - timedelta(days=1)).date()

    # Count metrics for yesterday
    total_views = BlogView.objects.filter(
        viewed_at__date=yesterday
    ).count()

    unique_visitors = VisitorSession.objects.filter(
        session_date=yesterday
    ).count()

    new_posts = Blog.objects.filter(
        status='published',
        published_at__date=yesterday
    ).count()

    new_subs = Subscriber.objects.filter(
        subscribed_at__date=yesterday
    ).count()

    new_contacts = ContactMessage.objects.filter(
        submitted_at__date=yesterday
    ).count()

    # Calculate storage (simplified - you can add actual file size calculation)
    total_files = Blog.objects.filter(status='published').count()

    # Create or update metrics
    SystemMetrics.objects.update_or_create(
        date=yesterday,
        defaults={
            'total_page_views': total_views,
            'unique_visitors': unique_visitors,
            'new_blog_posts': new_posts,
            'new_subscribers': new_subs,
            'new_contacts': new_contacts,
            'total_media_files': total_files,
            'total_storage_mb': 0.0,  # TODO: Implement actual calculation
        }
    )

    logger.info(f"Calculated system metrics for {yesterday}")


@shared_task(queue="analytics")
def cleanup_old_analytics():
    """
    Clean up old raw analytics data.
    Keep aggregated stats, delete raw events older than 90 days.
    Runs weekly via celery beat.
    """
    from .models import BlogView, VisitorSession

    cutoff = timezone.now() - timedelta(days=90)

    # Delete old blog views
    deleted_views, _ = BlogView.objects.filter(viewed_at__lt=cutoff).delete()

    # Delete old visitor sessions
    deleted_sessions, _ = VisitorSession.objects.filter(
        session_date__lt=cutoff.date()
    ).delete()

    logger.info(
        f"Cleaned up {deleted_views} old blog views and "
        f"{deleted_sessions} old visitor sessions"
    )

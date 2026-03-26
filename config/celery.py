"""
config/celery.py
=================
Celery app configuration with beat schedule.
"""
import os
from celery import Celery
from celery.schedules import crontab
from datetime import timedelta

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')

app = Celery('blog_backend')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()


app.conf.beat_schedule = {
    # Sync Redis view counter → DB every hour
    'sync-view-counts-hourly': {
        'task': 'apps.blog.tasks.sync_view_counts',
        'schedule': timedelta(hours=1),
    },
    # Rebuild sitemap every 6 hours
    'rebuild-sitemap-6h': {
        'task': 'apps.blog.tasks.rebuild_sitemap',
        'schedule': timedelta(hours=6),
    },
    # Rebuild RSS feed every 30 minutes
    'rebuild-rss-feed': {
        'task': 'apps.blog.tasks.rebuild_rss_feed',
        'schedule': timedelta(minutes=30),
    },
    # Aggregate analytics every hour
    'aggregate-analytics-hourly': {
        'task': 'apps.analytics.tasks.aggregate_hourly_stats',
        'schedule': timedelta(hours=1),
    },
    # Calculate trending posts daily
    'calculate-trending-daily': {
        'task': 'apps.analytics.tasks.calculate_trending_posts',
        'schedule': timedelta(days=1),
    },
    # Calculate system metrics daily
    'calculate-system-metrics-daily': {
        'task': 'apps.analytics.tasks.calculate_system_metrics',
        'schedule': timedelta(days=1),
    },
    # Clean up old analytics data weekly
    'cleanup-old-analytics-weekly': {
        'task': 'apps.analytics.tasks.cleanup_old_analytics',
        'schedule': timedelta(weeks=1),
    },
    # Weekly newsletter — Monday 9:00 AM
    'weekly-newsletter-monday': {
        'task': 'apps.newsletter.tasks.send_weekly_digest',
        'schedule': crontab(hour=9, minute=0, day_of_week=1),
    },
    # Clean old unconfirmed subscribers daily
    'cleanup-unconfirmed-daily': {
        'task': 'apps.newsletter.tasks.cleanup_unconfirmed',
        'schedule': timedelta(days=1),
    },
}

import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')

app = Celery('blog_backend')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()


app.conf.beat_schedule = {
  # ! ........... sync redis view counter --> DB every hour
  'sync-view-counts-hourly': {
    'task': 'apps.blog.tasks.sync_view  _counts',
    'schedule': timedelta(hours=1),
  },
  # ! ........... rebuild sitmap every 6 hours
  'rebuild-sitemap-6h': {
    'task': 'apps.blog.tasks.rebuild_sitemap',
    'schedule': timedelta(hours=6),
  },
  # ! .......... rebuild rss feed when new content published
  'rebuild-rss-feed': {
    'task': 'apps.blog.tasks.rebuild_rss_feed',
    'schedule': timedelta(minutes=30  ),
  },
  #! Aggregate analytics every hour
    'aggregate-analytics-hourly': {
        'task': 'apps.analytics.tasks.aggregate_hourly_stats',
        'schedule': timedelta(hours=1),
    },
    #! Weekly newsletter every Monday 9am
    'weekly-newsletter-monday': {
        'task': 'apps.newsletter.tasks.send_weekly_digest',
        'schedule': {'crontab': {'hour': 9, 'minute': 0, 'day_of_week': 1}},
    },
    #! Clean old unconfirmed subscribers daily
    'cleanup-unconfirmed-daily': {
        'task': 'apps.newsletter.tasks.cleanup_unconfirmed',
        'schedule': timedelta(days=1),
    },
}

"""
apps/analytics/models.py
=========================
Enhanced analytics system with visitor tracking.

Tables:
  BlogView        → Raw event log (one row per page view)
  HourlyBlogStat  → Pre-aggregated hourly summary
  VisitorSession  → Unique visitor tracking
  PopularContent  → Trending posts cache
"""

from django.db import models
from django.db.models import Q
from django.utils import timezone
from apps.blog.models import Blog


class BlogView(models.Model):
    """
    One row per unique blog view.
    IP is NEVER stored raw — only as a daily-rotating SHA-256 hash
    so we can deduplicate "viewed today" without storing personal data.
    This is fully GDPR-compliant.
    """

    blog = models.ForeignKey(
        Blog, on_delete=models.CASCADE, related_name="view_records"
    )

    # Hashed IP + daily salt (privacy-safe dedup)
    ip_hash = models.CharField(max_length=64, db_index=True)
    user_agent = models.CharField(max_length=255, blank=True)

    # Traffic source — populated from URL params or Referer header
    referrer = models.URLField(max_length=500, blank=True)
    utm_source = models.CharField(max_length=100, blank=True, db_index=True)
    utm_medium = models.CharField(max_length=100, blank=True, db_index=True)
    utm_campaign = models.CharField(max_length=100, blank=True)

    # Engagement signals — sent from frontend JS before page unload
    time_spent_seconds = models.PositiveIntegerField(default=0)
    scroll_depth_percent = models.PositiveSmallIntegerField(default=0)

    # Geographic data (optional, from IP geolocation)
    country_code = models.CharField(max_length=2, blank=True, db_index=True)
    city = models.CharField(max_length=100, blank=True)

    viewed_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        db_table = "blog_views"
        indexes = [
            models.Index(fields=["blog", "-viewed_at"], name="idx_view_blog_date"),
            models.Index(fields=["ip_hash", "blog"], name="idx_view_dedup"),
            models.Index(fields=["utm_source", "utm_medium"], name="idx_view_utm"),
            models.Index(fields=["-viewed_at"], name="idx_view_recent"),
        ]
        ordering = ['-viewed_at']

    def __str__(self):
        return f"View: {self.blog.slug} @ {self.viewed_at:%Y-%m-%d %H:%M}"


class HourlyBlogStat(models.Model):
    """
    Pre-aggregated hourly stats. Celery writes this every hour
    by grouping raw BlogView rows by (blog, hour).
    """

    blog = models.ForeignKey(
        Blog, on_delete=models.CASCADE, related_name="hourly_stats"
    )
    hour = models.DateTimeField(db_index=True)
    view_count = models.PositiveIntegerField(default=0)
    unique_visitors = models.PositiveIntegerField(default=0)
    avg_time_spent = models.PositiveIntegerField(default=0)
    avg_scroll_depth = models.PositiveSmallIntegerField(default=0)
    top_source = models.CharField(max_length=100, blank=True)

    class Meta:
        db_table = "hourly_blog_stats"
        unique_together = [["blog", "hour"]]
        indexes = [
            models.Index(fields=["-hour"], name="idx_hourly_stat_hour"),
            models.Index(fields=["blog", "-hour"], name="idx_hourly_blog_hour"),
        ]
        ordering = ['-hour']

    def __str__(self):
        return f"{self.blog.slug} @ {self.hour:%Y-%m-%d %H:00} — {self.view_count} views"


class VisitorSession(models.Model):
    """
    Track unique visitor sessions.
    One row per unique visitor per day.
    """

    ip_hash = models.CharField(max_length=64, db_index=True)
    session_date = models.DateField(db_index=True)

    # Session metadata
    first_seen = models.DateTimeField(auto_now_add=True)
    last_seen = models.DateTimeField(auto_now=True)
    page_views = models.PositiveIntegerField(default=1)

    # Device info
    device_type = models.CharField(
        max_length=20,
        choices=[
            ('mobile', 'Mobile'),
            ('tablet', 'Tablet'),
            ('desktop', 'Desktop'),
        ],
        default='desktop'
    )
    browser = models.CharField(max_length=50, blank=True)
    os = models.CharField(max_length=50, blank=True)

    # Geographic
    country_code = models.CharField(max_length=2, blank=True, db_index=True)

    class Meta:
        db_table = 'visitor_sessions'
        unique_together = [['ip_hash', 'session_date']]
        indexes = [
            models.Index(fields=['-session_date'], name='idx_session_date'),
            models.Index(fields=['ip_hash', '-session_date'], name='idx_session_visitor'),
        ]
        ordering = ['-session_date', '-last_seen']

    def __str__(self):
        return f"Session {self.ip_hash[:8]} on {self.session_date}"


class PopularContent(models.Model):
    """
    Cache of trending/popular posts.
    Updated by Celery task daily.
    """

    TIMEFRAME_CHOICES = [
        ('today', 'Today'),
        ('week', 'This Week'),
        ('month', 'This Month'),
        ('all_time', 'All Time'),
    ]

    blog = models.ForeignKey(Blog, on_delete=models.CASCADE, related_name='popularity_stats')
    timeframe = models.CharField(max_length=20, choices=TIMEFRAME_CHOICES, db_index=True)
    rank = models.PositiveIntegerField()
    view_count = models.PositiveIntegerField()
    unique_visitors = models.PositiveIntegerField(default=0)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'popular_content'
        unique_together = [['blog', 'timeframe']]
        indexes = [
            models.Index(fields=['timeframe', 'rank'], name='idx_popular_timeframe'),
        ]
        ordering = ['timeframe', 'rank']

    def __str__(self):
        return f"#{self.rank} {self.blog.title} ({self.timeframe})"

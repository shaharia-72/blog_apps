"""
apps/analytics/models.py
=========================
Two-table analytics design:

  BlogView        → Raw event log: one row per unique page view
  HourlyBlogStat  → Pre-aggregated hourly summary for fast dashboard queries

Why two tables?
  Reading 1,000,000 raw BlogView rows every dashboard load = slow.
  Aggregating into HourlyBlogStat (one row per blog per hour) = fast.
  Pattern: OLTP writes → Celery aggregation → OLAP reads.
"""

from django.db import models
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
    # e.g. ?utm_source=linkedin&utm_medium=post&utm_campaign=redis-article
    referrer = models.URLField(max_length=500, blank=True)
    utm_source = models.CharField(max_length=100, blank=True)
    utm_medium = models.CharField(max_length=100, blank=True)
    utm_campaign = models.CharField(max_length=100, blank=True)

    # Engagement signals — sent from frontend JS before page unload
    time_spent_seconds = models.PositiveIntegerField(default=0)
    scroll_depth_percent = models.PositiveSmallIntegerField(default=0)

    viewed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "blog_views"
        indexes = [
            # Most used query: "views for blog X in date range"
            models.Index(fields=["blog", "viewed_at"], name="idx_view_blog_date"),
            # Dedup check: "has this IP viewed this blog today?"
            models.Index(fields=["ip_hash", "blog"], name="idx_view_dedup"),
        ]

    def __str__(self):
        return f"View: {self.blog.slug} @ {self.viewed_at:%Y-%m-%d %H:%M}"


class HourlyBlogStat(models.Model):
    """
    Pre-aggregated hourly stats. Celery writes this every hour
    by grouping raw BlogView rows by (blog, hour).

    Dashboard queries hit this table instead of scanning millions
    of raw BlogView rows — queries go from seconds to milliseconds.
    """

    blog = models.ForeignKey(
        Blog, on_delete=models.CASCADE, related_name="hourly_stats"
    )
    hour = models.DateTimeField(db_index=True)  # Truncated to the hour
    view_count = models.PositiveIntegerField(default=0)
    top_source = models.CharField(max_length=100, blank=True)

    class Meta:
        db_table = "hourly_blog_stats"
        unique_together = [["blog", "hour"]]  # One row per blog per hour
        indexes = [
            models.Index(fields=["hour"], name="idx_hourly_stat_hour"),
        ]

    def __str__(self):
        return (
            f"{self.blog.slug} @ {self.hour:%Y-%m-%d %H:00} — {self.view_count} views"
        )

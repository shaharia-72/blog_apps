"""
apps/analytics/admin.py
"""

from django.contrib import admin
from .models import BlogView, HourlyBlogStat


@admin.register(BlogView)
class BlogViewAdmin(admin.ModelAdmin):
    list_display = [
        "blog",
        "viewed_at",
        "utm_source",
        "utm_medium",
        "time_spent_seconds",
        "scroll_depth_percent",
    ]
    list_filter = ["utm_source", "utm_medium", "viewed_at"]
    search_fields = ["blog__title", "utm_campaign"]
    readonly_fields = [
        "blog",
        "ip_hash",
        "user_agent",
        "referrer",
        "utm_source",
        "utm_medium",
        "utm_campaign",
        "time_spent_seconds",
        "scroll_depth_percent",
        "viewed_at",
    ]

    # Prevent accidental delete — analytics data is valuable
    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False


@admin.register(HourlyBlogStat)
class HourlyBlogStatAdmin(admin.ModelAdmin):
    list_display = ["blog", "hour", "view_count", "top_source"]
    list_filter = ["hour"]
    search_fields = ["blog__title"]
    readonly_fields = ["blog", "hour", "view_count", "top_source"]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

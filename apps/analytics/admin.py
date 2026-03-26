"""
apps/analytics/admin.py
========================
Admin for all analytics models including new VisitorSession and PopularContent.
"""

from django.contrib import admin
from .models import BlogView, HourlyBlogStat, VisitorSession, PopularContent


@admin.register(BlogView)
class BlogViewAdmin(admin.ModelAdmin):
    list_display = [
        "blog",
        "viewed_at",
        "utm_source",
        "utm_medium",
        "country_code",
        "time_spent_seconds",
        "scroll_depth_percent",
    ]
    list_filter = ["utm_source", "utm_medium", "country_code", "viewed_at"]
    search_fields = ["blog__title", "utm_campaign"]
    readonly_fields = [
        "blog", "ip_hash", "user_agent", "referrer",
        "utm_source", "utm_medium", "utm_campaign",
        "time_spent_seconds", "scroll_depth_percent",
        "country_code", "city", "viewed_at",
    ]
    date_hierarchy = "viewed_at"
    list_per_page = 50

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False


@admin.register(HourlyBlogStat)
class HourlyBlogStatAdmin(admin.ModelAdmin):
    list_display = ["blog", "hour", "view_count", "unique_visitors", "avg_time_spent", "top_source"]
    list_filter = ["hour"]
    search_fields = ["blog__title"]
    readonly_fields = ["blog", "hour", "view_count", "unique_visitors", "avg_time_spent", "avg_scroll_depth", "top_source"]
    date_hierarchy = "hour"

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False


@admin.register(VisitorSession)
class VisitorSessionAdmin(admin.ModelAdmin):
    list_display = ["ip_hash_short", "session_date", "page_views", "device_type", "country_code", "first_seen", "last_seen"]
    list_filter = ["device_type", "country_code", "session_date"]
    date_hierarchy = "session_date"
    list_per_page = 50

    def ip_hash_short(self, obj):
        return obj.ip_hash[:12] + "..."
    ip_hash_short.short_description = "Visitor"

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False


@admin.register(PopularContent)
class PopularContentAdmin(admin.ModelAdmin):
    list_display = ["rank", "blog", "timeframe", "view_count", "unique_visitors", "updated_at"]
    list_filter = ["timeframe"]
    search_fields = ["blog__title"]
    list_per_page = 50

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

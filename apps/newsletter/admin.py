"""
apps/newsletter/admin.py
"""

from django.contrib import admin
from django.utils.html import format_html
from .models import Subscriber


@admin.register(Subscriber)
class SubscriberAdmin(admin.ModelAdmin):
    list_display = ["email", "status_badge", "source", "subscribed_at", "confirmed_at"]
    list_filter = ["status", "source", "subscribed_at"]
    search_fields = ["email"]
    readonly_fields = ["subscribed_at", "confirmed_at", "unsubscribed_at"]
    ordering = ["-subscribed_at"]
    actions = ["mark_active", "mark_inactive"]

    def status_badge(self, obj):
        colors = {"active": "#28a745", "pending": "#ffc107", "inactive": "#6c757d"}
        color = colors.get(obj.status, "#000")
        return format_html(
            '<span style="background:{};color:#fff;padding:2px 8px;'
            'border-radius:10px;font-size:11px;font-weight:600">{}</span>',
            color,
            obj.status.upper(),
        )

    status_badge.short_description = "Status"

    def mark_active(self, request, queryset):
        from django.utils import timezone

        queryset.update(status="active", confirmed_at=timezone.now())
        self.message_user(request, f"Marked {queryset.count()} subscribers as active.")

    mark_active.short_description = "✅ Mark selected as active"

    def mark_inactive(self, request, queryset):
        queryset.update(status="inactive")
        self.message_user(request, f"Unsubscribed {queryset.count()} subscribers.")

    mark_inactive.short_description = "🚫 Unsubscribe selected"

"""
apps/contact/admin.py
======================
Django admin for contact inbox — your lead management panel.
"""

from django.contrib import admin
from django.utils.html import format_html
from django.utils import timezone
from .models import ContactMessage


@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = [
        "name",
        "email",
        "subject_short",
        "status_badge",
        "project_type",
        "budget",
        "submitted_at",
    ]
    list_filter = ["status", "project_type", "submitted_at"]
    search_fields = ["name", "email", "subject", "message", "company"]
    readonly_fields = [
        "name",
        "email",
        "subject",
        "message",
        "company",
        "budget",
        "project_type",
        "utm_source",
        "submitted_at",
        "replied_at",
    ]
    ordering = ["-submitted_at"]
    actions = ["mark_read", "mark_replied", "mark_archived"]

    fieldsets = [
        ("From", {"fields": ["name", "email", "company"]}),
        ("Message", {"fields": ["subject", "message"]}),
        ("Project Details", {"fields": ["project_type", "budget"]}),
        ("Pipeline", {"fields": ["status", "admin_notes", "replied_at"]}),
        ("Meta", {"classes": ["collapse"], "fields": ["utm_source", "submitted_at"]}),
    ]

    def subject_short(self, obj):
        return (obj.subject or "No subject")[:50]

    subject_short.short_description = "Subject"

    def status_badge(self, obj):
        colors = {
            "new": "#dc3545",
            "read": "#ffc107",
            "replied": "#28a745",
            "archived": "#6c757d",
        }
        color = colors.get(obj.status, "#000")
        return format_html(
            '<span style="background:{};color:#fff;padding:2px 10px;'
            'border-radius:10px;font-size:11px;font-weight:600">{}</span>',
            color,
            obj.status.upper(),
        )

    status_badge.short_description = "Status"

    def mark_read(self, request, queryset):
        queryset.filter(status="new").update(status="read")
        self.message_user(request, f"Marked {queryset.count()} message(s) as read.")

    mark_read.short_description = "👁️ Mark as read"

    def mark_replied(self, request, queryset):
        queryset.update(status="replied", replied_at=timezone.now())
        self.message_user(request, f"Marked {queryset.count()} message(s) as replied.")

    mark_replied.short_description = "✅ Mark as replied"

    def mark_archived(self, request, queryset):
        queryset.update(status="archived")
        self.message_user(request, f"Archived {queryset.count()} message(s).")

    mark_archived.short_description = "📦 Archive selected"

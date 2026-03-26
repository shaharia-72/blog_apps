"""
apps/projects/admin.py
"""

from django.contrib import admin
from .models import Project


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = [
        "title",
        "category",
        "is_featured",
        "is_active",
        "order",
        "created_at",
    ]
    list_filter = ["category", "is_featured", "is_active"]
    list_editable = ["order", "is_featured", "is_active"]
    search_fields = ["title", "description"]
    prepopulated_fields = {"slug": ("title",)}
    readonly_fields = ["slug", "created_at", "updated_at"]

    fieldsets = [
        (
            "Core",
            {"fields": ["title", "slug", "description", "highlights", "category"]},
        ),
        ("Media", {"fields": ["thumbnail", "screenshots"]}),
        ("Technical Details", {"fields": ["tech_stack", "features"]}),
        ("Links", {"fields": ["github_url", "live_url", "blog_url"]}),
        ("Display", {"fields": ["is_featured", "order", "is_active"]}),
        (
            "Timestamps",
            {"classes": ["collapse"], "fields": ["created_at", "updated_at"]},
        ),
    ]

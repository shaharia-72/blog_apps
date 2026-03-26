"""
apps/blog/admin.py
===================
Django admin configuration for Blog, Category, Tag.
The admin panel IS your CMS — write and publish blogs from here.
"""

from django.contrib import admin
from django.utils.html import format_html
from django.utils import timezone
from .models import Blog, BlogSection, Category, Tag
from core.utils import invalidate_blog_cache


# ── BlogSection inline ────────────────────────────────────────


class BlogSectionInline(admin.StackedInline):
    """
    Edit blog sections INSIDE the blog admin page.
    Add text, images, code blocks, and ads all from one screen.
    """

    model = BlogSection
    extra = 1
    ordering = ["order"]
    fields = [
        ("section_type", "order"),
        "content",
        ("image", "image_caption", "image_alt"),
        ("code_language", "code_filename"),
        ("ad_type", "ad_slot_id"),
        "ad_custom_html",
        "callout_type",
    ]


# ── Blog Admin ────────────────────────────────────────────────


@admin.register(Blog)
class BlogAdmin(admin.ModelAdmin):
    list_display = [
        "title",
        "status_badge",
        "category",
        "language",
        "views",
        "read_time",
        "is_featured",
        "published_at",
    ]
    list_filter = ["status", "language", "category", "is_featured", "published_at"]
    search_fields = ["title", "excerpt", "tags__name"]
    prepopulated_fields = {"slug": ("title",)}
    readonly_fields = ["views", "read_time", "created_at", "updated_at"]
    filter_horizontal = ["tags"]
    save_on_top = True  # Save button at top AND bottom

    fieldsets = [
        (
            "Content",
            {"fields": ["title", "slug", "language", "excerpt", "cover_image"]},
        ),
        ("Organisation", {"fields": ["author", "category", "tags"]}),
        (
            "Publishing",
            {"fields": ["status", "published_at", "is_featured", "featured_order"]},
        ),
        (
            "SEO",
            {
                "classes": ["collapse"],
                "fields": [
                    "seo_title",
                    "seo_description",
                    "seo_keywords",
                    "canonical_url",
                ],
                "description": "Leave blank to auto-fill from title / excerpt.",
            },
        ),
        (
            "Stats (read-only)",
            {
                "classes": ["collapse"],
                "fields": ["views", "read_time", "created_at", "updated_at"],
            },
        ),
    ]

    inlines = [BlogSectionInline]
    actions = ["publish_selected", "unpublish_selected", "archive_selected"]

    def status_badge(self, obj):
        """Color-coded status pill in the list view."""
        colors = {
            "published": "#28a745",
            "draft": "#ffc107",
            "archived": "#6c757d",
        }
        color = colors.get(obj.status, "#000")
        return format_html(
            '<span style="background:{};color:#fff;padding:3px 10px;'
            'border-radius:12px;font-size:11px;font-weight:600">{}</span>',
            color,
            obj.status.upper(),
        )

    status_badge.short_description = "Status"

    def publish_selected(self, request, queryset):
        count = queryset.filter(status="draft").update(
            status="published", published_at=timezone.now()
        )
        for blog in queryset:
            invalidate_blog_cache(blog.slug)
        self.message_user(request, f"✅ Published {count} post(s).")

    publish_selected.short_description = "✅ Publish selected"

    def unpublish_selected(self, request, queryset):
        count = queryset.filter(status="published").update(status="draft")
        for blog in queryset:
            invalidate_blog_cache(blog.slug)
        self.message_user(request, f"⬇️ Reverted {count} post(s) to draft.")

    unpublish_selected.short_description = "⬇️ Unpublish selected"

    def archive_selected(self, request, queryset):
        count = queryset.update(status="archived")
        self.message_user(request, f"📦 Archived {count} post(s).")

    archive_selected.short_description = "📦 Archive selected"


# ── Category Admin ────────────────────────────────────────────


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = [
        "name",
        "slug",
        "color_preview",
        "icon",
        "order",
        "blog_count",
        "is_active",
    ]
    list_editable = ["order", "is_active"]
    prepopulated_fields = {"slug": ("name",)}

    def color_preview(self, obj):
        return format_html(
            '<span style="background:{};display:inline-block;'
            "width:16px;height:16px;border-radius:3px;"
            'vertical-align:middle;margin-right:6px"></span>{}',
            obj.color,
            obj.color,
        )

    color_preview.short_description = "Color"

    def blog_count(self, obj):
        return obj.blogs.filter(status="published").count()

    blog_count.short_description = "Posts"


# ── Tag Admin ─────────────────────────────────────────────────


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ["name", "slug", "blog_count"]
    prepopulated_fields = {"slug": ("name",)}
    search_fields = ["name"]

    def blog_count(self, obj):
        return obj.blogs.filter(status="published").count()

    blog_count.short_description = "Posts"

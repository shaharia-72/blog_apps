"""
core/admin.py
=============
Admin interface for system-wide settings.
"""

from django.contrib import admin
from django.utils.html import format_html
from .models import StorageSettings, SystemMetrics


@admin.register(StorageSettings)
class StorageSettingsAdmin(admin.ModelAdmin):
    """
    Singleton admin for storage configuration.
    Admin can toggle between local and Cloudinary storage.
    """

    fieldsets = [
        ('Storage Backend', {
            'fields': ['storage_backend'],
            'description': 'Choose where to store uploaded media files.'
        }),
        ('Cloudinary Configuration', {
            'fields': [
                'cloudinary_cloud_name',
                'cloudinary_api_key',
                'cloudinary_api_secret',
            ],
            'classes': ['collapse'],
            'description': 'Required only if Cloudinary is selected above.',
        }),
        ('Upload Settings', {
            'fields': ['max_upload_size_mb', 'allowed_image_formats'],
        }),
        ('Metadata', {
            'fields': ['updated_at', 'updated_by'],
            'classes': ['collapse'],
        }),
    ]

    readonly_fields = ['updated_at', 'updated_by']

    def has_add_permission(self, request):
        """Prevent creating multiple instances."""
        return not StorageSettings.objects.exists()

    def has_delete_permission(self, request, obj=None):
        """Prevent deleting the singleton."""
        return False

    def save_model(self, request, obj, form, change):
        """Track who updated the settings."""
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(SystemMetrics)
class SystemMetricsAdmin(admin.ModelAdmin):
    """
    Read-only view of daily system metrics.
    Data populated by Celery tasks.
    """

    list_display = [
        'date',
        'total_page_views',
        'unique_visitors',
        'new_blog_posts',
        'new_subscribers',
        'storage_size',
    ]

    list_filter = ['date']
    ordering = ['-date']
    date_hierarchy = 'date'

    def storage_size(self, obj):
        """Format storage size."""
        if obj.total_storage_mb < 1024:
            return f"{obj.total_storage_mb:.1f} MB"
        return f"{obj.total_storage_mb / 1024:.1f} GB"

    storage_size.short_description = 'Storage Used'

    def has_add_permission(self, request):
        """Metrics are auto-generated."""
        return False

    def has_change_permission(self, request, obj=None):
        """Read-only."""
        return False

    def has_delete_permission(self, request, obj=None):
        """Allow cleanup of old metrics."""
        return request.user.is_superuser

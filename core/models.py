"""
core/models.py
==============
Core system settings and configurations.
"""

from django.db import models
from django.core.cache import cache


class StorageSettings(models.Model):
    """
    Global storage configuration.
    Admin can toggle between Cloudinary and local storage.
    Singleton model - only one instance exists.
    """

    STORAGE_CHOICES = [
        ('local', 'Local File System'),
        ('cloudinary', 'Cloudinary Cloud Storage'),
    ]

    storage_backend = models.CharField(
        max_length=20,
        choices=STORAGE_CHOICES,
        default='local',
        help_text="Choose where to store uploaded media files"
    )

    # Cloudinary credentials (only used if cloudinary is selected)
    cloudinary_cloud_name = models.CharField(max_length=200, blank=True)
    cloudinary_api_key = models.CharField(max_length=200, blank=True)
    cloudinary_api_secret = models.CharField(max_length=200, blank=True)

    # Settings
    max_upload_size_mb = models.PositiveIntegerField(
        default=10,
        help_text="Maximum file upload size in MB"
    )

    allowed_image_formats = models.JSONField(
        default=list,
        blank=True,
        help_text='Allowed image formats: ["jpg", "png", "webp"]'
    )

    # Metadata
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(
        'users.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='storage_updates'
    )

    class Meta:
        db_table = 'storage_settings'
        verbose_name = 'Storage Setting'
        verbose_name_plural = 'Storage Settings'

    def save(self, *args, **kwargs):
        """Ensure only one instance exists (singleton pattern)."""
        self.pk = 1
        super().save(*args, **kwargs)

        # Clear cache when settings change
        cache.delete('storage_settings')

    @classmethod
    def load(cls):
        """Load the singleton instance."""
        obj, created = cls.objects.get_or_create(pk=1)
        return obj

    def __str__(self):
        return f"Storage: {self.get_storage_backend_display()}"

    @property
    def is_cloudinary_enabled(self):
        """Check if Cloudinary is the active backend."""
        return self.storage_backend == 'cloudinary'


class SystemMetrics(models.Model):
    """
    System-wide metrics and statistics.
    Used for admin dashboard.
    """

    date = models.DateField(unique=True, db_index=True)

    # Traffic metrics
    total_page_views = models.PositiveIntegerField(default=0)
    unique_visitors = models.PositiveIntegerField(default=0)

    # Content metrics
    new_blog_posts = models.PositiveIntegerField(default=0)
    new_subscribers = models.PositiveIntegerField(default=0)
    new_contacts = models.PositiveIntegerField(default=0)

    # Storage metrics
    total_storage_mb = models.FloatField(default=0.0)
    total_media_files = models.PositiveIntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'system_metrics'
        ordering = ['-date']
        indexes = [
            models.Index(fields=['-date'], name='idx_metrics_date'),
        ]

    def __str__(self):
        return f"Metrics for {self.date}"

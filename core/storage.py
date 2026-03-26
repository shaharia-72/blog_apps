"""
core/storage.py
===============
Flexible media storage backend.
Admin can toggle between Cloudinary and local storage in settings.
"""

from django.conf import settings
from django.core.files.storage import FileSystemStorage
from storages.backends.s3boto3 import S3Boto3Storage


class MediaStorage(FileSystemStorage):
    """
    Default local media storage.
    Files stored in MEDIA_ROOT.
    """

    def __init__(self, *args, **kwargs):
        kwargs['location'] = settings.MEDIA_ROOT
        kwargs['base_url'] = settings.MEDIA_URL
        super().__init__(*args, **kwargs)


class CloudinaryMediaStorage:
    """
    Cloudinary cloud storage backend.
    Enabled when USE_CLOUDINARY=True in settings.
    """

    pass  # Handled by django-cloudinary-storage package


def get_storage_backend():
    """
    Returns the configured storage backend.
    Check settings.USE_CLOUDINARY to determine which to use.
    """
    if getattr(settings, 'USE_CLOUDINARY', False):
        from cloudinary_storage.storage import MediaCloudinaryStorage
        return MediaCloudinaryStorage()
    return MediaStorage()

"""
apps/blog/admin_urls.py
========================
Admin blog routes — all under /api/v1/admin/blogs/
JWT auth required via IsAdminUser permission.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import AdminBlogViewSet

router = DefaultRouter()
router.register(r"", AdminBlogViewSet, basename="admin-blog")

urlpatterns = router.urls

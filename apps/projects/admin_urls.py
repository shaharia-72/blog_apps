"""
apps/projects/admin_urls.py — Admin routes under /api/v1/admin/projects/
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import AdminProjectViewSet

router = DefaultRouter()
router.register(r"", AdminProjectViewSet, basename="admin-project")
urlpatterns = router.urls

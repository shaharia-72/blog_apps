"""
apps/contact/admin_urls.py
===========================
Admin contact inbox routes — /api/v1/admin/contact/
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import AdminContactViewSet

router = DefaultRouter()
router.register(r"", AdminContactViewSet, basename="admin-contact")
urlpatterns = router.urls

"""
apps/newsletter/admin_urls.py — Admin routes
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import AdminSubscriberViewSet

router = DefaultRouter()
router.register(r"subscribers", AdminSubscriberViewSet, basename="admin-subscribers")
urlpatterns = router.urls

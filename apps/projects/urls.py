"""
apps/projects/urls.py — Public routes
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ProjectViewSet

router = DefaultRouter()
router.register(r"", ProjectViewSet, basename="project")
urlpatterns = router.urls

"""
apps/blog/urls.py
==================
Public blog routes — all under /api/v1/blogs/
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import BlogViewSet, CategoryViewSet, TagViewSet

router = DefaultRouter()
router.register(r"categories", CategoryViewSet, basename="category")
router.register(r"tags", TagViewSet, basename="tag")
router.register(r"", BlogViewSet, basename="blog")

urlpatterns = router.urls

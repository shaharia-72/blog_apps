"""
apps/analytics/admin_urls.py — Admin analytics routes
"""

from django.urls import path
from .views import AdminDashboardView

urlpatterns = [
    path("dashboard/", AdminDashboardView.as_view(), name="admin-dashboard"),
]

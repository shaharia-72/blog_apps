"""
apps/analytics/urls.py — Public analytics routes
"""

from django.urls import path
from .views import PublicStatsView

urlpatterns = [
    path("stats/", PublicStatsView.as_view(), name="public-stats"),
]

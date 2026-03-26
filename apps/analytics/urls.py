"""
apps/analytics/urls.py — Public analytics routes
"""

from django.urls import path
from .views import PublicStatsView, TrendingPostsView

urlpatterns = [
    path("stats/", PublicStatsView.as_view(), name="public-stats"),
    path("trending/", TrendingPostsView.as_view(), name="trending-posts"),
]

"""
core/ads_urls.py
=================
Serves /ads.txt — required by Google AdSense for ad verification.
"""

from django.urls import path
from .ads_views import AdsTxtView

urlpatterns = [
    path('', AdsTxtView.as_view(), name='ads-txt'),
]

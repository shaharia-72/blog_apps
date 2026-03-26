"""
apps/monetization/urls.py — Public routes
"""
from django.urls import path
from .views import AffiliateRedirectView, AdSlotsView

urlpatterns = [
    path('slots/', AdSlotsView.as_view(), name='ad-slots'),
]

# Note: /go/<slug>/ is registered at root level in config/urls.py

"""
apps/newsletter/urls.py — Public routes
"""

from django.urls import path
from .views import SubscribeView, ConfirmSubscriptionView, UnsubscribeView

urlpatterns = [
    path("subscribe/", SubscribeView.as_view(), name="newsletter-subscribe"),
    path(
        "confirm/<str:token>/",
        ConfirmSubscriptionView.as_view(),
        name="newsletter-confirm",
    ),
    path("unsubscribe/", UnsubscribeView.as_view(), name="newsletter-unsubscribe"),
]

"""
apps/monetization/admin_urls.py
"""
from django.urls import path
from .views import AdminRevenueDashboardView, AdminAffiliateListView

urlpatterns = [
    path('revenue/', AdminRevenueDashboardView.as_view(), name='admin-revenue'),
    path('affiliates/', AdminAffiliateListView.as_view(), name='admin-affiliates'),
]

"""
apps/users/urls.py
===================
Auth endpoints — all under /api/v1/admin/auth/
"""

from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from .views import AdminLoginView, AdminLogoutView, AdminProfileView

urlpatterns = [
    path("login/", AdminLoginView.as_view(), name="admin-login"),
    path("logout/", AdminLogoutView.as_view(), name="admin-logout"),
    path("refresh/", TokenRefreshView.as_view(), name="token-refresh"),
    path("profile/", AdminProfileView.as_view(), name="admin-profile"),
]

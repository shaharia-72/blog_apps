"""
apps/users/views.py
====================
Admin authentication and profile management views.
Clean, secure, production-ready version.
"""

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated

from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError

from django.contrib.auth import get_user_model

from .serializers import (
    AdminProfileSerializer,
    AdminTokenObtainPairSerializer,
)
from core.permissions import IsAdminUser
from drf_spectacular.utils import extend_schema

User = get_user_model()


# =========================================================
# 🔐 ADMIN LOGIN VIEW
# =========================================================
@extend_schema(tags=["Auth"])
class AdminLoginView(TokenObtainPairView):
    """
    POST /api/v1/admin/auth/login/

    Body:
    {
        "username": "admin",
        "password": "yourpassword"
    }

    Returns:
    - access token
    - refresh token
    - user info

    Only allows admin users (is_staff=True)
    """

    serializer_class = AdminTokenObtainPairSerializer


# =========================================================
# 🚪 ADMIN LOGOUT VIEW
# =========================================================
@extend_schema(tags=["Auth"])
class AdminLogoutView(APIView):
    """
    POST /api/v1/admin/auth/logout/

    Body:
    {
        "refresh": "your_refresh_token"
    }

    Blacklists the refresh token (true logout)
    """

    permission_classes = [IsAuthenticated]

    def post(self, request):
        refresh_token = request.data.get("refresh")

        # 🔍 Validate input
        if not refresh_token:
            return Response(
                {"error": "Refresh token is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            # 🔐 Create token object
            token = RefreshToken(refresh_token)

            # 🚫 Blacklist token
            token.blacklist()

            return Response(
                {"message": "Logged out successfully."},
                status=status.HTTP_200_OK,
            )

        except TokenError:
            return Response(
                {"error": "Invalid or expired token."},
                status=status.HTTP_400_BAD_REQUEST,
            )


# =========================================================
# 👤 ADMIN PROFILE VIEW
# =========================================================
@extend_schema(tags=["Admin"])
class AdminProfileView(APIView):
    """
    GET    /api/v1/admin/auth/profile/   → Get profile
    PATCH  /api/v1/admin/auth/profile/   → Update profile
    """

    permission_classes = [IsAdminUser]

    def get(self, request):
        """
        Get current admin profile
        """
        serializer = AdminProfileSerializer(request.user, context={"request": request})
        return Response(serializer.data, status=status.HTTP_200_OK)

    def patch(self, request):
        """
        Update admin profile (partial update)
        """
        serializer = AdminProfileSerializer(
            request.user, data=request.data, partial=True, context={"request": request}
        )

        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(serializer.data, status=status.HTTP_200_OK)

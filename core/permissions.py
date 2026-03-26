# ! custom DRF permission class
from rest_framework.permissions import BasePermission, SAFE_METHODS


class IsAdminOrReadonly(BasePermission):
    """
    GET / HEAD / OPTIONS → anyone
    POST / PUT / PATCH / DELETE → is_staff only
    """

    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        return bool(request.user and request.user.is_staff)


class IsAdminUser(BasePermission):
    def has_permission(self, request, view):
        return bool(
            request.user and request.user.is_authenticated and request.user.is_staff
        )


class IsOwnerOrAdmin(BasePermission):
    """Object-level: owner or staff only."""

    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True
        return obj == request.user or request.user.is_staff

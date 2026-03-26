"""
apps/projects/views.py
"""

from rest_framework import viewsets
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from django.core.cache import cache

from .models import Project
from .serializers import (
    ProjectListSerializer,
    ProjectDetailSerializer,
    ProjectWriteSerializer,
)
from core.permissions import IsAdminUser

PROJECTS_CACHE_TTL = 60 * 60  # 1 hour


class ProjectViewSet(viewsets.ReadOnlyModelViewSet):
    """
    GET /api/v1/projects/        → All active projects
    GET /api/v1/projects/{slug}/ → Single project detail
    ?category=backend  → Filter by category
    ?featured=true     → Featured only
    """

    permission_classes = [AllowAny]
    lookup_field = "slug"
    filterset_fields = ["category", "is_featured"]

    def get_queryset(self):
        return Project.objects.filter(is_active=True)

    def get_serializer_class(self):
        return (
            ProjectDetailSerializer
            if self.action == "retrieve"
            else ProjectListSerializer
        )

    def list(self, request, *args, **kwargs):
        qs = request.META.get("QUERY_STRING", "")
        cache_key = f"projects:list:{hash(qs)}"
        cached = cache.get(cache_key)
        if cached:
            return Response(cached)
        response = super().list(request, *args, **kwargs)
        cache.set(cache_key, response.data, PROJECTS_CACHE_TTL)
        return response


class AdminProjectViewSet(viewsets.ModelViewSet):
    """Full CRUD for admin."""

    permission_classes = [IsAdminUser]
    queryset = Project.objects.all().order_by("-updated_at")

    def get_serializer_class(self):
        if self.action in ["list", "retrieve"]:
            return ProjectDetailSerializer
        return ProjectWriteSerializer

    def _clear_cache(self):
        try:
            cache.delete_pattern("projects:list:*")
        except Exception:
            cache.delete("projects:list:")

    def perform_create(self, serializer):
        serializer.save()
        self._clear_cache()

    def perform_update(self, serializer):
        serializer.save()
        self._clear_cache()

    def perform_destroy(self, instance):
        instance.delete()
        self._clear_cache()

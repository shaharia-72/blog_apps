"""
apps/projects/serializers.py
"""

from rest_framework import serializers
from .models import Project


class ProjectListSerializer(serializers.ModelSerializer):
    """Lightweight for project grid cards."""

    thumbnail_url = serializers.SerializerMethodField()

    class Meta:
        model = Project
        fields = [
            "id",
            "title",
            "slug",
            "description",
            "category",
            "thumbnail_url",
            "tech_stack",
            "github_url",
            "live_url",
            "is_featured",
        ]

    def get_thumbnail_url(self, obj):
        request = self.context.get("request")
        if obj.thumbnail and request:
            return request.build_absolute_uri(obj.thumbnail.url)
        return None


class ProjectDetailSerializer(serializers.ModelSerializer):
    """Full project detail with related projects."""

    thumbnail_url = serializers.SerializerMethodField()
    related_projects = serializers.SerializerMethodField()

    class Meta:
        model = Project
        fields = [
            "id",
            "title",
            "slug",
            "description",
            "highlights",
            "category",
            "thumbnail_url",
            "screenshots",
            "tech_stack",
            "features",
            "github_url",
            "live_url",
            "blog_url",
            "is_featured",
            "created_at",
            "related_projects",
        ]

    def get_thumbnail_url(self, obj):
        request = self.context.get("request")
        if obj.thumbnail and request:
            return request.build_absolute_uri(obj.thumbnail.url)
        return None

    def get_related_projects(self, obj):
        """Same category, max 3, excluding current."""
        related = (
            Project.objects.filter(is_active=True, category=obj.category)
            .exclude(id=obj.id)
            .order_by("order")[:3]
        )
        return ProjectListSerializer(related, many=True, context=self.context).data


class ProjectWriteSerializer(serializers.ModelSerializer):
    """Admin create/update."""

    class Meta:
        model = Project
        exclude = ["slug"]

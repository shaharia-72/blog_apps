"""
apps/blog/filters.py
=====================
URL query-param filters for the blog list endpoint.

Examples:
  GET /api/v1/blogs/?category=backend
  GET /api/v1/blogs/?tag=redis
  GET /api/v1/blogs/?language=en
  GET /api/v1/blogs/?featured=true
"""

import django_filters
from .models import Blog


class BlogFilter(django_filters.FilterSet):
    category = django_filters.CharFilter(
        field_name="category__slug",
        lookup_expr="exact",
        label="Filter by category slug",
    )
    tag = django_filters.CharFilter(
        field_name="tags__slug", lookup_expr="exact", label="Filter by tag slug"
    )
    language = django_filters.CharFilter(field_name="language", lookup_expr="exact")
    featured = django_filters.BooleanFilter(field_name="is_featured")

    class Meta:
        model = Blog
        fields = ["category", "tag", "language", "featured"]

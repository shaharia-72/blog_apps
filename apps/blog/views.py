"""
apps/blog/views.py
===================
Public and admin blog endpoints.

Caching strategy:
  Blog list   → cached 10 min in Redis (key includes all query params)
  Blog detail → cached 30 min in Redis
  View counts → Redis atomic counter, batch-flushed to DB every hour
  Featured    → cached 10 min
"""

import hashlib
import logging
from django.conf import settings
from django.core.cache import cache
from django.db import models
from django.db.models import Count, Q, Avg
from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django_filters.rest_framework import DjangoFilterBackend

from .models import Blog, Category, Tag
from .serializers import (
    BlogListSerializer,
    BlogDetailSerializer,
    BlogWriteSerializer,
    CategoryListSerializer,
    CategoryDetailSerializer,
    TagSerializer,
)
from .filters import BlogFilter
from core.permissions import IsAdminUser
from core.pagination import StandardPagination, LargePagination
from core.utils import get_client_ip, hash_ip, invalidate_blog_cache

logger = logging.getLogger(__name__)

LIST_TTL = settings.BLOG_SETTINGS["CACHE_BLOG_LIST_TTL"]
DETAIL_TTL = settings.BLOG_SETTINGS["CACHE_BLOG_DETAIL_TTL"]


from drf_spectacular.utils import extend_schema, extend_schema_view


# ── Public Blog ViewSet ───────────────────────────────────────


@extend_schema_view(
    list=extend_schema(tags=["Blog"]),
    retrieve=extend_schema(tags=["Blog"]),
    featured=extend_schema(tags=["Blog"]),
    view=extend_schema(tags=["Blog"]),
    stats=extend_schema(tags=["Blog"]),
)
class BlogViewSet(viewsets.ReadOnlyModelViewSet):
    """
    GET /api/v1/blogs/              → Paginated, filterable blog list
    GET /api/v1/blogs/{slug}/       → Full blog detail
    GET /api/v1/blogs/featured/     → Featured posts for homepage
    POST /api/v1/blogs/{slug}/view/ → Track a view (deduped by IP+day)
    GET /api/v1/blogs/{slug}/stats/ → Engagement stats for a post
    """

    permission_classes = [AllowAny]
    pagination_class = StandardPagination
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_class = BlogFilter
    search_fields = ["title", "excerpt", "tags__name", "category__name"]
    ordering_fields = ["published_at", "views", "read_time", "title"]
    ordering = ["-published_at"]
    lookup_field = "slug"

    def get_queryset(self):
        """
        Only published posts.
        select_related → join author+category in ONE SQL query (no N+1).
        prefetch_related → M2M tags in ONE extra query (not per-post).
        only() → SELECT only needed columns (faster than SELECT *).
        """
        return (
            Blog.objects.published()
            .select_related("author", "category")
            .prefetch_related("tags")
            .only(
                "id",
                "title",
                "slug",
                "language",
                "excerpt",
                "cover_image",
                "is_featured",
                "featured_order",
                "views",
                "read_time",
                "published_at",
                "status",
                "author__first_name",
                "author__last_name",
                "author__avatar",
                "category__name",
                "category__slug",
                "category__color",
                "category__icon",
            )
        )

    def get_serializer_class(self):
        return BlogDetailSerializer if self.action == "retrieve" else BlogListSerializer

    def list(self, request, *args, **kwargs):
        """
        Cache the entire paginated response in Redis.
        Cache key is unique per combination of query params
        so ?category=backend and ?tag=redis have separate caches.
        """
        qs = request.META.get("QUERY_STRING", "")
        cache_key = f"blog:list:{hashlib.md5(qs.encode()).hexdigest()}"

        cached = cache.get(cache_key)
        if cached:
            return Response(cached)

        response = super().list(request, *args, **kwargs)
        cache.set(cache_key, response.data, LIST_TTL)
        return response

    def retrieve(self, request, *args, **kwargs):
        """Cache single blog detail for 30 minutes."""
        slug = kwargs.get("slug")
        cache_key = f"blog:detail:{slug}"

        cached = cache.get(cache_key)
        if cached:
            return Response(cached)

        response = super().retrieve(request, *args, **kwargs)
        cache.set(cache_key, response.data, DETAIL_TTL)
        return response

    @action(detail=False, methods=["get"])
    def featured(self, request):
        """GET /api/v1/blogs/featured/ — Homepage featured posts."""
        cached = cache.get("blog:featured")
        if cached:
            return Response(cached)

        count = settings.BLOG_SETTINGS.get("FEATURED_POSTS_COUNT", 6)
        blogs = Blog.objects.featured()[:count]
        data = BlogListSerializer(blogs, many=True, context={"request": request}).data
        cache.set("blog:featured", data, LIST_TTL)
        return Response(data)

    @action(detail=True, methods=["post"])
    def view(self, request, slug=None):
        """
        POST /api/v1/blogs/{slug}/view/
        Dedup logic:
          1. Hash visitor IP + today's date → daily-unique token
          2. Check Redis: already viewed today?
          3. If new: increment Redis counter + queue DB write via Celery
          4. Celery batch-flushes counters to DB every hour
        This pattern handles high traffic without DB pressure.
        """
        blog = self.get_object()
        ip = get_client_ip(request)
        ip_hash = hash_ip(ip)
        dedup_key = f"view:dedup:{blog.id}:{ip_hash}"

        if not cache.get(dedup_key):
            cache.set(dedup_key, 1, 86400)  # Expires tomorrow
            cache.incr(f"blog:views:{blog.id}")  # Atomic Redis increment

            from apps.analytics.tasks import record_blog_view

            record_blog_view.delay(
                blog_id=blog.id,
                ip_hash=ip_hash,
                user_agent=request.META.get("HTTP_USER_AGENT", "")[:255],
                referrer=request.data.get("referrer", ""),
                utm_source=request.data.get("utm_source", ""),
                utm_medium=request.data.get("utm_medium", ""),
                utm_campaign=request.data.get("utm_campaign", ""),
            )

        redis_extra = int(cache.get(f"blog:views:{blog.id}") or 0)
        current_views = blog.views + redis_extra
        return Response({"views": current_views})

    @action(detail=True, methods=["get"])
    def stats(self, request, slug=None):
        """GET /api/v1/blogs/{slug}/stats/ — Public engagement stats."""
        blog = self.get_object()
        cache_key = f"blog:stats:{blog.id}"

        cached = cache.get(cache_key)
        if cached:
            return Response(cached)

        from apps.analytics.models import BlogView

        agg = BlogView.objects.filter(blog=blog).aggregate(
            avg_time=Avg("time_spent_seconds"),
            avg_scroll=Avg("scroll_depth_percent"),
        )
        data = {
            "views": blog.views,
            "avg_time_spent_seconds": int(agg["avg_time"] or 0),
            "avg_scroll_depth_percent": int(agg["avg_scroll"] or 0),
        }
        cache.set(cache_key, data, settings.BLOG_SETTINGS["CACHE_ANALYTICS_TTL"])
        return Response(data)


# ── Public Category ViewSet ───────────────────────────────────


@extend_schema_view(
    list=extend_schema(tags=["Blog"]),
    retrieve=extend_schema(tags=["Blog"]),
)
class CategoryViewSet(viewsets.ReadOnlyModelViewSet):
    """
    GET /api/v1/blogs/categories/        → All active categories
    GET /api/v1/blogs/categories/{slug}/ → Category detail
    """

    queryset = Category.objects.filter(is_active=True).annotate(
        blog_count=Count("blogs", filter=Q(blogs__status="published"))
    )
    lookup_field = "slug"
    permission_classes = [AllowAny]
    pagination_class = None  # Return all — there won't be many categories

    def get_serializer_class(self):
        return (
            CategoryDetailSerializer
            if self.action == "retrieve"
            else CategoryListSerializer
        )


# ── Public Tag ViewSet ────────────────────────────────────────


@extend_schema_view(
    list=extend_schema(tags=["Blog"]),
    retrieve=extend_schema(tags=["Blog"]),
)
class TagViewSet(viewsets.ReadOnlyModelViewSet):
    """GET /api/v1/blogs/tags/ — Tags that have at least one published post."""

    queryset = Tag.objects.annotate(
        blog_count=Count("blogs", filter=Q(blogs__status="published"))
    ).filter(blog_count__gt=0)
    serializer_class = TagSerializer
    permission_classes = [AllowAny]
    pagination_class = None
    lookup_field = "slug"


# ── Admin Blog ViewSet ────────────────────────────────────────


@extend_schema_view(
    list=extend_schema(tags=["Admin"]),
    create=extend_schema(tags=["Admin"]),
    retrieve=extend_schema(tags=["Admin"]),
    update=extend_schema(tags=["Admin"]),
    partial_update=extend_schema(tags=["Admin"]),
    destroy=extend_schema(tags=["Admin"]),
    publish=extend_schema(tags=["Admin"]),
    unpublish=extend_schema(tags=["Admin"]),
)
class AdminBlogViewSet(viewsets.ModelViewSet):
    """
    Full CRUD for admin. Sees ALL posts including drafts.

    GET    /api/v1/admin/blogs/               → All posts (filter by ?status=)
    POST   /api/v1/admin/blogs/               → Create new post
    PUT    /api/v1/admin/blogs/{id}/          → Full update
    PATCH  /api/v1/admin/blogs/{id}/          → Partial update
    DELETE /api/v1/admin/blogs/{id}/          → Delete
    PATCH  /api/v1/admin/blogs/{id}/publish/  → Publish a draft
    PATCH  /api/v1/admin/blogs/{id}/unpublish/ → Revert to draft
    """

    permission_classes = [IsAdminUser]
    pagination_class = LargePagination

    def get_queryset(self):
        qs = (
            Blog.objects.all()
            .select_related("author", "category")
            .prefetch_related("tags", "sections")
            .order_by("-updated_at")
        )
        status_filter = self.request.query_params.get("status")
        if status_filter:
            qs = qs.filter(status=status_filter)
        return qs

    def get_serializer_class(self):
        if self.action in ["create", "update", "partial_update"]:
            return BlogWriteSerializer
        return BlogDetailSerializer

    def perform_destroy(self, instance):
        invalidate_blog_cache(instance.slug)
        instance.delete()

    def perform_update(self, serializer):
        instance = serializer.save()
        invalidate_blog_cache(instance.slug)

    @action(detail=True, methods=["patch"])
    def publish(self, request, pk=None):
        blog = self.get_object()
        blog.status = "published"
        blog.save()
        invalidate_blog_cache(blog.slug)
        return Response({"status": "published", "published_at": blog.published_at})

    @action(detail=True, methods=["patch"])
    def unpublish(self, request, pk=None):
        blog = self.get_object()
        blog.status = "draft"
        blog.save()
        invalidate_blog_cache(blog.slug)
        return Response({"status": "draft"})

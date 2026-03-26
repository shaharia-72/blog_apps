"""
apps/analytics/views.py
========================
Public stats endpoint + admin dashboard endpoint.
"""

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django.core.cache import cache
from django.conf import settings
from django.db import models
from django.db.models import Sum
from django.utils import timezone
from datetime import timedelta

from core.permissions import IsAdminUser


class PublicStatsView(APIView):
    """
    GET /api/v1/analytics/stats/
    High-level public counters shown on the homepage / about page.
    Cached 1 hour — these numbers don't need to be real-time.
    """

    permission_classes = [AllowAny]

    def get(self, request):
        cache_key = "analytics:public_stats"
        cached = cache.get(cache_key)
        if cached:
            return Response(cached)

        from apps.blog.models import Blog, Category
        from apps.projects.models import Project

        total_views = (
            Blog.objects.filter(status="published").aggregate(t=Sum("views"))["t"] or 0
        )

        stats = {
            "total_blogs": Blog.objects.filter(status="published").count(),
            "total_views": total_views,
            "total_projects": Project.objects.filter(is_active=True).count(),
            "categories": list(
                Category.objects.filter(is_active=True)
                .annotate(
                    count=models.Count(
                        "blogs", filter=models.Q(blogs__status="published")
                    )
                )
                .filter(count__gt=0)
                .values("name", "slug", "color", "icon", "count")
            ),
        }

        cache.set(cache_key, stats, settings.BLOG_SETTINGS["CACHE_ANALYTICS_TTL"])
        return Response(stats)


class AdminDashboardView(APIView):
    """
    GET /api/v1/admin/analytics/dashboard/
    Full metrics for the admin dashboard panel.
    Includes: views, subscriber counts, top posts, unread contacts.
    """

    permission_classes = [IsAdminUser]

    def get(self, request):
        from apps.blog.models import Blog
        from apps.newsletter.models import Subscriber
        from apps.contact.models import ContactMessage

        week_ago = timezone.now() - timedelta(days=7)
        today_start = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)

        # Top 5 posts by all-time views
        top_blogs = list(
            Blog.objects.filter(status="published")
            .order_by("-views")[:5]
            .values("title", "slug", "views", "published_at")
        )

        data = {
            "total_views": Blog.objects.filter(status="published").aggregate(
                t=Sum("views")
            )["t"]
            or 0,
            "total_blogs": Blog.objects.count(),
            "published_blogs": Blog.objects.filter(status="published").count(),
            "draft_blogs": Blog.objects.filter(status="draft").count(),
            "archived_blogs": Blog.objects.filter(status="archived").count(),
            "total_subscribers": Subscriber.objects.filter(status="active").count(),
            "pending_subscribers": Subscriber.objects.filter(status="pending").count(),
            "new_subscribers_week": Subscriber.objects.filter(
                subscribed_at__gte=week_ago
            ).count(),
            "total_contacts": ContactMessage.objects.count(),
            "new_contacts": ContactMessage.objects.filter(status="new").count(),
            "top_blogs": top_blogs,
        }
        return Response(data)

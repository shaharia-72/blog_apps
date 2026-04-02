"""
apps/analytics/views.py
========================
Enhanced analytics endpoints with comprehensive dashboard.
"""

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django.core.cache import cache
from django.conf import settings
from django.db import models
from django.db.models import Sum, Count, Avg, Q
from django.utils import timezone
from datetime import timedelta, date

from core.permissions import IsAdminUser
from .models import BlogView, HourlyBlogStat, VisitorSession, PopularContent
from drf_spectacular.utils import extend_schema


@extend_schema(tags=["Analytics"])
class PublicStatsView(APIView):
    """
    GET /api/v1/analytics/stats/
    High-level public counters shown on homepage/about page.
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
            Blog.objects.filter(status="published")
            .aggregate(t=Sum("views"))["t"] or 0
        )

        stats = {
            "total_blogs": Blog.objects.filter(status="published").count(),
            "total_views": total_views,
            "total_projects": Project.objects.filter(is_active=True).count(),
            "categories": list(
                Category.objects.filter(is_active=True)
                .annotate(
                    count=Count(
                        "blogs",
                        filter=Q(blogs__status="published")
                    )
                )
                .filter(count__gt=0)
                .values("name", "slug", "color", "icon", "count")
                .order_by("-count")
            ),
        }

        cache.set(cache_key, stats, settings.BLOG_SETTINGS["CACHE_ANALYTICS_TTL"])
        return Response(stats)


class AdminDashboardView(APIView):
    """
    GET /api/v1/admin/analytics/dashboard/
    Comprehensive admin dashboard with all metrics.
    """

    permission_classes = [IsAdminUser]

    def get(self, request):
        cache_key = "admin:dashboard"
        cached = cache.get(cache_key)
        if cached:
            return Response(cached)

        from apps.blog.models import Blog
        from apps.newsletter.models import Subscriber
        from apps.contact.models import ContactMessage
        from core.models import SystemMetrics

        now = timezone.now()
        today = now.date()
        week_ago = now - timedelta(days=7)
        month_ago = now - timedelta(days=30)

        # ══════════════════════════════════════════════════════
        # 📊 OVERVIEW METRICS
        # ══════════════════════════════════════════════════════

        total_views = Blog.objects.filter(
            status="published"
        ).aggregate(t=Sum("views"))["t"] or 0

        # Unique visitors today
        visitors_today = VisitorSession.objects.filter(
            session_date=today
        ).count()

        # Unique visitors this week
        visitors_week = VisitorSession.objects.filter(
            session_date__gte=(now - timedelta(days=7)).date()
        ).values('ip_hash').distinct().count()

        # ══════════════════════════════════════════════════════
        # 📝 CONTENT METRICS
        # ══════════════════════════════════════════════════════

        content_stats = {
            "total_blogs": Blog.objects.count(),
            "published_blogs": Blog.objects.filter(status="published").count(),
            "draft_blogs": Blog.objects.filter(status="draft").count(),
            "archived_blogs": Blog.objects.filter(status="archived").count(),
            "blogs_this_week": Blog.objects.filter(
                created_at__gte=week_ago
            ).count(),
            "blogs_this_month": Blog.objects.filter(
                created_at__gte=month_ago
            ).count(),
        }

        # ══════════════════════════════════════════════════════
        # 👥 AUDIENCE METRICS
        # ══════════════════════════════════════════════════════

        audience_stats = {
            "total_subscribers": Subscriber.objects.filter(
                status="active"
            ).count(),
            "pending_subscribers": Subscriber.objects.filter(
                status="pending"
            ).count(),
            "new_subscribers_week": Subscriber.objects.filter(
                subscribed_at__gte=week_ago
            ).count(),
            "new_subscribers_month": Subscriber.objects.filter(
                subscribed_at__gte=month_ago
            ).count(),
        }

        # ══════════════════════════════════════════════════════
        # 💬 CONTACT METRICS
        # ══════════════════════════════════════════════════════

        contact_stats = {
            "total_contacts": ContactMessage.objects.count(),
            "new_contacts": ContactMessage.objects.filter(
                status="new"
            ).count(),
            "contacts_this_week": ContactMessage.objects.filter(
                submitted_at__gte=week_ago
            ).count(),
            "contacts_this_month": ContactMessage.objects.filter(
                submitted_at__gte=month_ago
            ).count(),
        }

        # ══════════════════════════════════════════════════════
        # 🔥 TRENDING POSTS
        # ══════════════════════════════════════════════════════

        trending_today = list(
            PopularContent.objects.filter(timeframe='today')
            .select_related('blog')
            .order_by('rank')[:5]
            .values(
                'blog__title',
                'blog__slug',
                'view_count',
                'unique_visitors',
                'rank'
            )
        )

        trending_week = list(
            PopularContent.objects.filter(timeframe='week')
            .select_related('blog')
            .order_by('rank')[:5]
            .values(
                'blog__title',
                'blog__slug',
                'view_count',
                'unique_visitors',
                'rank'
            )
        )

        # ══════════════════════════════════════════════════════
        # 📈 TRAFFIC SOURCES
        # ══════════════════════════════════════════════════════

        traffic_sources = list(
            BlogView.objects.filter(
                viewed_at__gte=week_ago
            )
            .exclude(utm_source='')
            .values('utm_source')
            .annotate(count=Count('id'))
            .order_by('-count')[:10]
        )

        # ══════════════════════════════════════════════════════
        # 🌍 GEOGRAPHIC DATA
        # ══════════════════════════════════════════════════════

        top_countries = list(
            VisitorSession.objects.filter(
                session_date__gte=(now - timedelta(days=30)).date()
            )
            .exclude(country_code='')
            .values('country_code')
            .annotate(visitors=Count('id'))
            .order_by('-visitors')[:10]
        )

        # ══════════════════════════════════════════════════════
        # 📊 ENGAGEMENT METRICS
        # ══════════════════════════════════════════════════════

        engagement = BlogView.objects.filter(
            viewed_at__gte=week_ago
        ).aggregate(
            avg_time_spent=Avg('time_spent_seconds'),
            avg_scroll_depth=Avg('scroll_depth_percent'),
        )

        # ══════════════════════════════════════════════════════
        # 📅 DAILY TRENDS (Last 30 Days)
        # ══════════════════════════════════════════════════════

        daily_stats = list(
            SystemMetrics.objects.filter(
                date__gte=(now - timedelta(days=30)).date()
            )
            .order_by('date')
            .values(
                'date',
                'total_page_views',
                'unique_visitors',
                'new_blog_posts',
                'new_subscribers'
            )
        )

        # ══════════════════════════════════════════════════════
        # 🎯 RESPONSE DATA
        # ══════════════════════════════════════════════════════

        data = {
            "overview": {
                "total_views": total_views,
                "visitors_today": visitors_today,
                "visitors_week": visitors_week,
            },
            "content": content_stats,
            "audience": audience_stats,
            "contacts": contact_stats,
            "trending": {
                "today": trending_today,
                "week": trending_week,
            },
            "traffic_sources": traffic_sources,
            "top_countries": top_countries,
            "engagement": {
                "avg_time_spent_seconds": int(engagement['avg_time_spent'] or 0),
                "avg_scroll_depth_percent": int(engagement['avg_scroll_depth'] or 0),
            },
            "daily_trends": daily_stats,
        }

        cache.set(cache_key, data, 60)  # 1 minute cache
        return Response(data)


class TrendingPostsView(APIView):
    """
    GET /api/v1/analytics/trending/?timeframe=week
    Get trending posts for a specific timeframe.
    """

    permission_classes = [AllowAny]

    def get(self, request):
        timeframe = request.query_params.get('timeframe', 'week')

        if timeframe not in ['today', 'week', 'month', 'all_time']:
            timeframe = 'week'

        trending = list(
            PopularContent.objects.filter(timeframe=timeframe)
            .select_related('blog', 'blog__category', 'blog__author')
            .order_by('rank')[:20]
            .values(
                'rank',
                'view_count',
                'unique_visitors',
                'blog__id',
                'blog__title',
                'blog__slug',
                'blog__excerpt',
                'blog__category__name',
                'blog__category__slug',
                'blog__read_time',
            )
        )

        return Response({
            'timeframe': timeframe,
            'count': len(trending),
            'results': trending,
        })

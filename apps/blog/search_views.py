"""
apps/blog/search_views.py
==========================
Global search across blog posts.
GET /api/v1/search/?q=redis+caching

FIX H1: Upgraded from icontains (SQL LIKE '%query%' — can't use indexes)
        to PostgreSQL full-text search (SearchVector + SearchRank).
        Falls back to icontains for SQLite (dev mode).
FIX H2: Added Redis caching for search results (5 minute TTL).
"""

import hashlib

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django.db.models import Q
from django.core.cache import cache

from .models import Blog
from .serializers import BlogListSerializer
from core.pagination import StandardPagination

SEARCH_CACHE_TTL = 60 * 5  # 5 minutes


class SearchView(APIView):
    """
    Full-text search across title, excerpt, tags, and categories.

    PostgreSQL mode (production):
      Uses SearchVector + SearchRank for relevance-ranked results.
      Results are ordered by relevance, not just date.

    SQLite mode (dev fallback):
      Uses icontains for basic matching.
    """

    permission_classes = [AllowAny]

    def get(self, request):
        query = request.GET.get("q", "").strip()

        if len(query) < 2:
            return Response(
                {
                    "query": query,
                    "count": 0,
                    "results": [],
                    "hint": "Query must be at least 2 characters.",
                }
            )

        # Check cache first
        cache_key = f"search:{hashlib.md5(query.lower().encode()).hexdigest()}"
        cached = cache.get(cache_key)
        if cached:
            cached["from_cache"] = True
            return Response(cached)

        results = self._search(query)

        paginator = StandardPagination()
        page = paginator.paginate_queryset(results, request)
        serializer = BlogListSerializer(page, many=True, context={"request": request})
        response = paginator.get_paginated_response(serializer.data)
        response.data["query"] = query

        # Cache the result
        cache.set(cache_key, response.data, SEARCH_CACHE_TTL)
        return response

    def _search(self, query):
        """
        Try PostgreSQL full-text search first.
        Fall back to icontains for SQLite (development).
        """
        try:
            return self._postgres_search(query)
        except Exception:
            return self._fallback_search(query)

    def _postgres_search(self, query):
        """
        PostgreSQL SearchVector + SearchRank.
        Weights: title (A=1.0) > excerpt (B=0.4) > tags (C=0.2)
        """
        from django.contrib.postgres.search import (
            SearchVector,
            SearchQuery,
            SearchRank,
        )

        search_query = SearchQuery(query, search_type="websearch")
        search_vector = (
            SearchVector("title", weight="A")
            + SearchVector("excerpt", weight="B")
        )

        return (
            Blog.objects.published()
            .annotate(
                search=search_vector,
                rank=SearchRank(search_vector, search_query),
            )
            .filter(
                Q(search=search_query)
                | Q(tags__name__icontains=query)
                | Q(category__name__icontains=query)
            )
            .distinct()
            .select_related("author", "category")
            .prefetch_related("tags")
            .order_by("-rank", "-published_at")
        )

    def _fallback_search(self, query):
        """icontains fallback for SQLite (development)."""
        return (
            Blog.objects.published()
            .filter(
                Q(title__icontains=query)
                | Q(excerpt__icontains=query)
                | Q(tags__name__icontains=query)
                | Q(category__name__icontains=query)
            )
            .distinct()
            .select_related("author", "category")
            .prefetch_related("tags")
            .order_by("-published_at")
        )

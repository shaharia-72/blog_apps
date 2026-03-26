"""
apps/blog/search_views.py
==========================
Global search across blog posts.
GET /api/v1/search/?q=redis+caching
"""

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django.db.models import Q

from .models import Blog
from .serializers import BlogListSerializer
from core.pagination import StandardPagination


class SearchView(APIView):
    """
    Full-text search across title, excerpt, tags, and categories.

    Searches:
      title__icontains       → "redis caching best practices"
      excerpt__icontains     → short description match
      tags__name__icontains  → tag label match
      category__name__icontains → category match

    .distinct() prevents duplicate results when a post matches
    multiple tags in the query.

    Future upgrade: replace icontains with PostgreSQL SearchVector
    + SearchRank for proper relevance-ranked full-text search.
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

        results = (
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

        paginator = StandardPagination()
        page = paginator.paginate_queryset(results, request)
        serializer = BlogListSerializer(page, many=True, context={"request": request})
        response = paginator.get_paginated_response(serializer.data)
        response.data["query"] = query
        return response

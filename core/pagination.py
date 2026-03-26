"""
core/pagination.py
===================
Custom paginators for all list endpoints.
"""

from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response


class StandardPagination(PageNumberPagination):
    """
    Default for all public list endpoints.
    ?page=2&page_size=20
    Max 50 items — prevent abuse.
    """

    page_size = 10
    page_size_query_param = "page_size"
    max_page_size = 50
    page_query_param = "page"

    def get_paginated_response(self, data):
        return Response(
            {
                "count": self.page.paginator.count,
                "total_pages": self.page.paginator.num_pages,
                "current_page": self.page.number,
                "next": self.get_next_link(),
                "previous": self.get_previous_link(),
                "results": data,
            }
        )


class LargePagination(PageNumberPagination):
    """For admin endpoints that need more rows at once."""

    page_size = 25
    page_size_query_param = "page_size"
    max_page_size = 100

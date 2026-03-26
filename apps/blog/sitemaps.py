"""
apps/blog/sitemaps.py
======================
Django sitemaps — generates /sitemap.xml automatically.
Submit the sitemap URL to Google Search Console for faster indexing.

Priority guide:
  1.0 = most important (homepage)
  0.8 = blog posts (main content — high value)
  0.6 = categories
  0.5 = static pages
"""

from django.contrib.sitemaps import Sitemap
from django.conf import settings
from .models import Blog, Category


class BlogSitemap(Sitemap):
    """
    One entry per published blog post.
    Google uses lastmod to detect when content changed
    and prioritise recrawling.
    """

    changefreq = "weekly"
    priority = 0.8

    def items(self):
        return Blog.objects.published().order_by("-updated_at")

    def lastmod(self, obj):
        return obj.updated_at

    def location(self, obj):
        return f"/blog/{obj.slug}/"


class CategorySitemap(Sitemap):
    """One entry per active category page."""

    changefreq = "weekly"
    priority = 0.6

    def items(self):
        return Category.objects.filter(is_active=True)

    def lastmod(self, obj):
        return obj.updated_at

    def location(self, obj):
        return f"/blog/category/{obj.slug}/"


class StaticViewSitemap(Sitemap):
    """Static pages: homepage, blog index, projects, contact."""

    changefreq = "monthly"
    priority = 0.5

    def items(self):
        return [
            ("/", 1.0),  # Homepage — highest priority
            ("/blog/", 0.9),  # Blog index
            ("/projects/", 0.6),
            ("/contact/", 0.4),
            ("/about/", 0.4),
        ]

    def location(self, item):
        return item[0]

    def priority(self, item):
        return item[1]

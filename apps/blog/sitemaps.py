"""
apps/blog/sitemaps.py
======================
Django sitemaps — generates /sitemap.xml automatically.

FIX: Removed duplicate class-level `priority = 0.5` from StaticViewSitemap.
     The priority() METHOD already handles priorities per item.
     Having both the attribute AND the method causes the method to be
     silently shadowed in some Django versions.
"""

from django.contrib.sitemaps import Sitemap
from .models import Blog, Category


class BlogSitemap(Sitemap):
    changefreq = "weekly"
    priority = 0.8
    i18n = True # FIX M15: Enables multilingual hreflang variations if USE_I18N=True

    def items(self):
        return Blog.objects.published().order_by("-updated_at")

    def lastmod(self, obj):
        return obj.updated_at

    def location(self, obj):
        # When i18n=True, Django automatically prefixes the lang code if translation active
        return f"/blog/{obj.slug}/"


class CategorySitemap(Sitemap):
    changefreq = "weekly"
    priority = 0.6
    i18n = True

    def items(self):
        return Category.objects.filter(is_active=True)

    def lastmod(self, obj):
        return obj.updated_at

    def location(self, obj):
        return f"/blog/category/{obj.slug}/"


class StaticViewSitemap(Sitemap):
    """
    Static pages: homepage, blog index, projects, contact.
    FIX: Removed `priority = 0.5` class attribute — it conflicts with the
    priority() method below. The method already returns per-item priorities.
    """

    changefreq = "monthly"
    i18n = True
    # NOTE: Do NOT add `priority = 0.5` here — the method below handles it.

    def items(self):
        return [
            ("/", 1.0),
            ("/blog/", 0.9),
            ("/projects/", 0.6),
            ("/contact/", 0.4),
            ("/about/", 0.4),
        ]

    def location(self, item):
        return item[0]

    def priority(self, item):
        return item[1]

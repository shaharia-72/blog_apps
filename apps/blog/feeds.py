"""
apps/blog/feeds.py
===================
RSS 2.0 feeds — important for SEO:
  - Google uses RSS to discover new posts faster
  - Readers subscribe for repeat traffic
  - RSS is a "freshness signal" for indexing

Endpoints:
  /feed/              → Latest posts across all categories
  /feed/<slug>/       → Posts from one specific category
"""

from django.contrib.syndication.views import Feed
from django.conf import settings
from django.utils.feedgenerator import Rss201rev2Feed
from .models import Blog, Category


class LatestBlogsFeed(Feed):
    """
    /feed/
    Latest 20 posts across all categories.
    Google Discover and RSS readers use this.
    """

    feed_type = Rss201rev2Feed
    title = settings.FEED_SETTINGS["TITLE"]
    description = settings.FEED_SETTINGS["DESCRIPTION"]
    link = "/"

    def items(self):
        count = settings.FEED_SETTINGS.get("ITEMS_COUNT", 20)
        return Blog.objects.published().order_by("-published_at")[:count]

    def item_title(self, item):
        return item.title

    def item_description(self, item):
        return item.excerpt

    def item_pubdate(self, item):
        return item.published_at

    def item_updateddate(self, item):
        return item.updated_at

    def item_link(self, item):
        """Absolute URL for the blog post on frontend."""
        return f"{settings.SEO_SETTINGS['SITE_URL']}/blog/{item.slug}/"

    def item_author_name(self, item):
        return item.author.get_full_name() or item.author.username

    def item_categories(self, item):
        """Tags shown as feed categories."""
        return [t.name for t in item.tags.all()]


class CategoryBlogsFeed(Feed):
    """
    /feed/<slug>/
    Latest posts from a specific category.
    Useful for readers who only follow e.g. AI/ML posts.
    """

    feed_type = Rss201rev2Feed

    def get_object(self, request, slug):
        return Category.objects.get(slug=slug, is_active=True)

    def title(self, obj):
        site = settings.SEO_SETTINGS["SITE_NAME"]
        return f"{obj.name} — {site}"

    def description(self, obj):
        return (
            obj.description
            or f'Latest {obj.name} posts from {settings.SEO_SETTINGS["SITE_NAME"]}'
        )

    def link(self, obj):
        return f"/blog/category/{obj.slug}/"

    def items(self, obj):
        count = settings.FEED_SETTINGS.get("ITEMS_COUNT", 20)
        return (
            Blog.objects.published()
            .filter(category=obj)
            .order_by("-published_at")[:count]
        )

    def item_title(self, item):
        return item.title

    def item_description(self, item):
        return item.excerpt

    def item_pubdate(self, item):
        return item.published_at

    def item_updateddate(self, item):
        return item.updated_at

    def item_link(self, item):
        return f"{settings.SEO_SETTINGS['SITE_URL']}/blog/{item.slug}/"

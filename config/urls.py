"""
config/urls.py
===============
Main URL router. All API routes live under /api/v1/.
Versioning makes future /api/v2/ upgrades easy.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.sitemaps.views import sitemap
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView

from apps.blog.sitemaps import BlogSitemap, CategorySitemap, StaticViewSitemap
from apps.blog.feeds import LatestBlogsFeed, CategoryBlogsFeed

# All sitemap classes registered here
sitemaps = {
    'blogs':      BlogSitemap,
    'categories': CategorySitemap,
    'static':     StaticViewSitemap,
}

urlpatterns = [
    # ── Django Admin ──────────────────────────────────────────
    path('admin/', admin.site.urls),

    # ── Public API ────────────────────────────────────────────
    path('api/v1/', include([
        path('blogs/',      include('apps.blog.urls')),
        path('projects/',   include('apps.projects.urls')),
        path('newsletter/', include('apps.newsletter.urls')),
        path('contact/',    include('apps.contact.urls')),
        path('analytics/',  include('apps.analytics.urls')),
        path('search/',     include('apps.blog.search_urls')),
    ])),

    # ── Admin API (JWT protected) ─────────────────────────────
    path('api/v1/admin/', include([
        path('auth/',       include('apps.users.urls')),
        path('blogs/',      include('apps.blog.admin_urls')),
        path('projects/',   include('apps.projects.admin_urls')),
        path('newsletter/', include('apps.newsletter.admin_urls')),
        path('contact/',    include('apps.contact.admin_urls')),
        path('analytics/',  include('apps.analytics.admin_urls')),
    ])),

    # ── SEO ───────────────────────────────────────────────────
    # Sitemap: submit to Google Search Console → /sitemap.xml
    path('sitemap.xml', sitemap, {'sitemaps': sitemaps}, name='sitemap'),

    # RSS feeds — Google indexes RSS for "freshness" signals
    path('feed/',               LatestBlogsFeed(),                 name='rss-feed'),
    path('feed/<slug:slug>/',   CategoryBlogsFeed(),               name='rss-feed-category'),

    # robots.txt — managed via django-robots (admin UI)
    path('robots.txt', include('robots.urls')),

    # ── API Docs ──────────────────────────────────────────────
    path('api/schema/',  SpectacularAPIView.as_view(),             name='schema'),
    path('api/docs/',    SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/redoc/',   SpectacularRedocView.as_view(url_name='schema'),  name='redoc'),
]

# Serve media files locally in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL,  document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

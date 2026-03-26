"""
config/urls.py
===============
UPDATED: Added monetization routes (/go/<slug>/ and /api/v1/ads/).
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.sitemaps.views import sitemap
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView

from apps.blog.sitemaps import BlogSitemap, CategorySitemap, StaticViewSitemap
from apps.blog.feeds import LatestBlogsFeed, CategoryBlogsFeed
from apps.monetization.views import AffiliateRedirectView

sitemaps = {
    'blogs':      BlogSitemap,
    'categories': CategorySitemap,
    'static':     StaticViewSitemap,
}

urlpatterns = [
    # ── Django Admin ──────────────────────────────────────────
    path('admin/', admin.site.urls),

    # ── Affiliate redirect (tracked) ─────────────────────────
    # Link in posts: <a href="/go/hostinger-vps">Get Hostinger</a>
    path('go/<slug:slug>/', AffiliateRedirectView.as_view(), name='affiliate-redirect'),

    # ── Public API ────────────────────────────────────────────
    path('api/v1/', include([
        path('blogs/',        include('apps.blog.urls')),
        path('projects/',     include('apps.projects.urls')),
        path('newsletter/',   include('apps.newsletter.urls')),
        path('contact/',      include('apps.contact.urls')),
        path('analytics/',    include('apps.analytics.urls')),
        path('search/',       include('apps.blog.search_urls')),
        path('ads/',          include('apps.monetization.urls')),
    ])),

    # ── Admin API (JWT protected) ─────────────────────────────
    path('api/v1/admin/', include([
        path('auth/',         include('apps.users.urls')),
        path('blogs/',        include('apps.blog.admin_urls')),
        path('projects/',     include('apps.projects.admin_urls')),
        path('newsletter/',   include('apps.newsletter.admin_urls')),
        path('contact/',      include('apps.contact.admin_urls')),
        path('analytics/',    include('apps.analytics.admin_urls')),
        path('monetization/', include('apps.monetization.admin_urls')),
    ])),

    # ── SEO ───────────────────────────────────────────────────
    path('sitemap.xml', sitemap, {'sitemaps': sitemaps}, name='sitemap'),
    path('feed/',               LatestBlogsFeed(),                 name='rss-feed'),
    path('feed/<slug:slug>/',   CategoryBlogsFeed(),               name='rss-feed-category'),
    path('robots.txt',          include('robots.urls')),

    # ── API Docs ──────────────────────────────────────────────
    path('api/schema/',  SpectacularAPIView.as_view(),             name='schema'),
    path('api/docs/',    SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/redoc/',   SpectacularRedocView.as_view(url_name='schema'),  name='redoc'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL,  document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

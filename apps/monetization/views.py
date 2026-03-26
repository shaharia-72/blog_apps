"""
apps/monetization/views.py
===========================
Affiliate link redirect, ad slot config API, revenue dashboard.
"""

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django.shortcuts import redirect, get_object_or_404
from django.core.cache import cache
from django.db.models import Sum, Count
from django.utils import timezone
from datetime import timedelta

from core.permissions import IsAdminUser
from core.utils import get_client_ip, hash_ip
from .models import AffiliateLink, AffiliateLinkClick, AdSlot, RevenueEvent


class AffiliateRedirectView(APIView):
    """
    GET /go/<slug>/
    Tracks the click then 302 redirects to the affiliate URL.
    Frontend links like: <a href="/go/hostinger-vps">Get Hostinger</a>
    """

    permission_classes = [AllowAny]

    def get(self, request, slug):
        link = get_object_or_404(AffiliateLink, slug=slug, is_active=True)

        # Dedup clicks by IP+day — same as blog view dedup
        ip = get_client_ip(request)
        ip_hash = hash_ip(ip)
        dedup_key = f"aff:click:{link.id}:{ip_hash}"

        if not cache.get(dedup_key):
            cache.set(dedup_key, 1, 86400)

            # Log the click
            AffiliateLinkClick.objects.create(
                link=link,
                ip_hash=ip_hash,
                referrer=request.META.get('HTTP_REFERER', '')[:500],
                user_agent=request.META.get('HTTP_USER_AGENT', '')[:255],
            )

            # Atomic increment
            AffiliateLink.objects.filter(id=link.id).update(
                click_count=link.click_count + 1  # safe because we deduplicated above
            )

        return redirect(link.destination_url, permanent=False)


class AdSlotsView(APIView):
    """
    GET /api/v1/ads/slots/
    Returns active ad slot config for frontend to render ads.
    Frontend fetches this once on load and uses slot_key to place ads.
    Cached 1 hour — ad config rarely changes.
    """

    permission_classes = [AllowAny]

    def get(self, request):
        cached = cache.get('ads:slots')
        if cached:
            return Response(cached)

        slots = list(
            AdSlot.objects.filter(is_active=True)
            .values(
                'slot_key', 'slot_type', 'placement',
                'adsense_publisher_id', 'adsense_slot_id',
                'adsense_format', 'custom_html',
            )
        )

        # Index by slot_key so frontend can do slots['mid-content-1']
        data = {s['slot_key']: s for s in slots}
        cache.set('ads:slots', data, 60 * 60)
        return Response(data)


class AdminRevenueDashboardView(APIView):
    """
    GET /api/v1/admin/monetization/revenue/
    Revenue summary for admin dashboard.
    """

    permission_classes = [IsAdminUser]

    def get(self, request):
        now = timezone.now()
        month_ago = now - timedelta(days=30)
        year_ago = now - timedelta(days=365)

        # Total earnings by source
        by_source = list(
            RevenueEvent.objects
            .values('source')
            .annotate(total=Sum('amount_usd'), count=Count('id'))
            .order_by('-total')
        )

        # Monthly totals (last 12 months)
        monthly = list(
            RevenueEvent.objects
            .filter(event_date__gte=year_ago.date())
            .extra(select={'month': "DATE_TRUNC('month', event_date)"})
            .values('month')
            .annotate(total=Sum('amount_usd'))
            .order_by('month')
        )

        # Top affiliate links
        top_affiliates = list(
            AffiliateLink.objects
            .filter(is_active=True)
            .order_by('-click_count')[:10]
            .values(
                'name', 'slug', 'click_count',
                'conversion_count', 'estimated_earnings_usd'
            )
        )

        # This month total
        this_month = RevenueEvent.objects.filter(
            event_date__gte=month_ago.date()
        ).aggregate(total=Sum('amount_usd'))['total'] or 0

        # All-time total
        all_time = RevenueEvent.objects.aggregate(
            total=Sum('amount_usd')
        )['total'] or 0

        return Response({
            'summary': {
                'this_month_usd': float(this_month),
                'all_time_usd': float(all_time),
            },
            'by_source': by_source,
            'monthly_trend': monthly,
            'top_affiliates': top_affiliates,
        })


class AdminAffiliateListView(APIView):
    """
    GET  /api/v1/admin/monetization/affiliates/
    POST /api/v1/admin/monetization/affiliates/
    Manage affiliate links from admin.
    """

    permission_classes = [IsAdminUser]

    def get(self, request):
        links = list(
            AffiliateLink.objects
            .values(
                'id', 'name', 'slug', 'destination_url',
                'click_count', 'conversion_count',
                'estimated_earnings_usd', 'is_active',
            )
            .order_by('-click_count')
        )
        return Response({'count': len(links), 'results': links})

    def post(self, request):
        from .serializers import AffiliateLinkWriteSerializer
        serializer = AffiliateLinkWriteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        link = serializer.save()
        return Response({'id': link.id, 'slug': link.slug}, status=201)

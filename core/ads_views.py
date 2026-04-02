"""
core/ads_views.py
==================
Serves /ads.txt for Google AdSense verification.

Google requires this file at your domain root to verify you own the site.
Without it, ad serving may be restricted or disabled.

How to use:
  1. Sign up for Google AdSense at https://www.google.com/adsense
  2. Get your publisher ID (starts with ca-pub-)
  3. Set ADSENSE_PUBLISHER_ID in your .env file
  4. ads.txt will be served automatically at yourdomain.com/ads.txt
"""

from django.http import HttpResponse
from django.conf import settings
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from drf_spectacular.utils import extend_schema


@extend_schema(tags=["Monetization"])
class AdsTxtView(APIView):
    """
    GET /ads.txt
    Returns the ads.txt content required by Google AdSense.
    Content-Type: text/plain (not JSON).
    """

    permission_classes = [AllowAny]
    authentication_classes = []

    def get(self, request):
        publisher_id = getattr(settings, 'ADSENSE_PUBLISHER_ID', '')

        if publisher_id:
            content = f"google.com, {publisher_id}, DIRECT, f08c47fec0942fa0\n"
        else:
            # Placeholder — update after getting AdSense account
            content = (
                "# ads.txt — Update with your Google AdSense publisher ID\n"
                "# Format: google.com, ca-pub-XXXXXXXXXXXXXXXX, DIRECT, f08c47fec0942fa0\n"
            )

        return HttpResponse(content, content_type="text/plain")

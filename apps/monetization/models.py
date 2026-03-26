"""
apps/monetization/models.py
============================
Phase 3: Monetization features.

Models:
  AffiliateLink   → Track affiliate clicks + conversions
  AdSlot          → Manage AdSense / custom ad placements
  PremiumPost     → Gated content for paying subscribers (future)
  RevenueEvent    → Log every revenue-related event for reporting
"""

from django.db import models
from django.utils import timezone
from apps.blog.models import Blog


class AffiliateLink(models.Model):
    """
    Affiliate link tracker.
    Every affiliate URL goes through /go/<slug>/ which:
      1. Records the click
      2. Redirects to destination
    This lets you see which posts/links earn money.
    """

    name = models.CharField(max_length=200, help_text="Internal name, e.g. 'Hostinger VPS'")
    slug = models.SlugField(unique=True, help_text="Used in /go/<slug>/ redirect URL")
    destination_url = models.URLField(help_text="The actual affiliate URL with your tracking ID")

    # Which blog post this link is associated with (optional)
    blog = models.ForeignKey(
        Blog,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='affiliate_links',
    )

    # Stats
    click_count = models.PositiveIntegerField(default=0)
    conversion_count = models.PositiveIntegerField(default=0)
    estimated_earnings_usd = models.DecimalField(
        max_digits=10, decimal_places=2, default=0.00,
        help_text="Manually update from your affiliate dashboard"
    )

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'affiliate_links'
        ordering = ['-click_count']

    def __str__(self):
        return f"{self.name} ({self.click_count} clicks)"

    @property
    def conversion_rate(self):
        if self.click_count == 0:
            return 0
        return round((self.conversion_count / self.click_count) * 100, 2)


class AffiliateLinkClick(models.Model):
    """
    Raw click log for affiliate links.
    One row per click. Used for fraud detection and reporting.
    """

    link = models.ForeignKey(AffiliateLink, on_delete=models.CASCADE, related_name='clicks')
    ip_hash = models.CharField(max_length=64)
    referrer = models.URLField(max_length=500, blank=True)
    user_agent = models.CharField(max_length=255, blank=True)
    clicked_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'affiliate_clicks'
        indexes = [
            models.Index(fields=['link', '-clicked_at'], name='idx_aff_click_link'),
            models.Index(fields=['-clicked_at'], name='idx_aff_click_date'),
        ]
        ordering = ['-clicked_at']

    def __str__(self):
        return f"Click on {self.link.name} at {self.clicked_at:%Y-%m-%d %H:%M}"


class AdSlot(models.Model):
    """
    Manage your AdSense / custom ad slots from admin.
    Reference these by slot_key in blog sections instead of
    hardcoding ad IDs in the frontend.
    """

    SLOT_TYPES = [
        ('adsense_auto', 'AdSense Auto Ads'),
        ('adsense_display', 'AdSense Display'),
        ('adsense_in_article', 'AdSense In-Article'),
        ('adsense_in_feed', 'AdSense In-Feed'),
        ('custom_html', 'Custom HTML Banner'),
        ('affiliate_banner', 'Affiliate Banner'),
    ]

    PLACEMENT_CHOICES = [
        ('header', 'Above Header'),
        ('after_intro', 'After Introduction (Section 2)'),
        ('mid_content', 'Mid Content'),
        ('before_conclusion', 'Before Conclusion'),
        ('sidebar', 'Sidebar'),
        ('footer', 'Footer'),
    ]

    slot_key = models.CharField(max_length=50, unique=True, help_text="Reference key used in API, e.g. 'mid-content-1'")
    slot_type = models.CharField(max_length=30, choices=SLOT_TYPES)
    placement = models.CharField(max_length=30, choices=PLACEMENT_CHOICES)

    # AdSense fields
    adsense_publisher_id = models.CharField(
        max_length=100, blank=True,
        help_text="ca-pub-XXXXXXXXXXXXXXXX"
    )
    adsense_slot_id = models.CharField(
        max_length=50, blank=True,
        help_text="Your AdSense data-ad-slot ID"
    )
    adsense_format = models.CharField(
        max_length=30, blank=True,
        default='auto',
        help_text="auto, rectangle, vertical, horizontal"
    )

    # Custom HTML (for affiliate banners etc.)
    custom_html = models.TextField(blank=True)

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'ad_slots'
        ordering = ['placement']

    def __str__(self):
        return f"{self.slot_key} ({self.slot_type}) — {self.placement}"


class RevenueEvent(models.Model):
    """
    Manual revenue logging.
    Log payouts from AdSense, affiliates, sponsors here
    to track total blog earnings over time.
    """

    SOURCE_CHOICES = [
        ('adsense', 'Google AdSense'),
        ('affiliate', 'Affiliate Commission'),
        ('sponsor', 'Sponsorship'),
        ('other', 'Other'),
    ]

    source = models.CharField(max_length=20, choices=SOURCE_CHOICES)
    amount_usd = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.CharField(max_length=300)
    event_date = models.DateField(default=timezone.now)

    # Optional link to affiliate or blog
    affiliate_link = models.ForeignKey(
        AffiliateLink, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='revenue_events'
    )
    blog = models.ForeignKey(
        Blog, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='revenue_events'
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'revenue_events'
        ordering = ['-event_date']

    def __str__(self):
        return f"${self.amount_usd} from {self.source} on {self.event_date}"

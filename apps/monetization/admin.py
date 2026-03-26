"""
apps/monetization/admin.py
"""
from django.contrib import admin
from django.utils.html import format_html
from .models import AffiliateLink, AffiliateLinkClick, AdSlot, RevenueEvent


@admin.register(AffiliateLink)
class AffiliateLinkAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'click_count', 'conversion_count', 'conversion_rate_display', 'estimated_earnings_usd', 'is_active']
    list_filter = ['is_active']
    search_fields = ['name', 'slug', 'destination_url']
    readonly_fields = ['click_count', 'conversion_count', 'created_at']

    def conversion_rate_display(self, obj):
        return f"{obj.conversion_rate}%"
    conversion_rate_display.short_description = "Conv. Rate"


@admin.register(AdSlot)
class AdSlotAdmin(admin.ModelAdmin):
    list_display = ['slot_key', 'slot_type', 'placement', 'is_active']
    list_filter = ['slot_type', 'placement', 'is_active']
    list_editable = ['is_active']


@admin.register(RevenueEvent)
class RevenueEventAdmin(admin.ModelAdmin):
    list_display = ['event_date', 'source', 'amount_usd', 'description']
    list_filter = ['source', 'event_date']
    ordering = ['-event_date']
    date_hierarchy = 'event_date'

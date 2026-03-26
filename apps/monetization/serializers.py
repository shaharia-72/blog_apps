"""
apps/monetization/serializers.py
"""
from rest_framework import serializers
from .models import AffiliateLink, AdSlot, RevenueEvent


class AffiliateLinkWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = AffiliateLink
        fields = [
            'name', 'slug', 'destination_url', 'blog',
            'estimated_earnings_usd', 'is_active'
        ]


class AdSlotWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = AdSlot
        fields = '__all__'


class RevenueEventWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = RevenueEvent
        fields = '__all__'

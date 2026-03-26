"""
apps/newsletter/serializers.py
"""

from rest_framework import serializers
from .models import Subscriber


class SubscribeSerializer(serializers.Serializer):
    """Validate and normalise subscription request data."""

    email = serializers.EmailField()
    source = serializers.CharField(max_length=100, required=False, default="")

    def validate_email(self, value):
        # Always lowercase and strip whitespace
        return value.lower().strip()


class SubscriberAdminSerializer(serializers.ModelSerializer):
    """Full subscriber data for admin list / export."""

    class Meta:
        model = Subscriber
        fields = "__all__"

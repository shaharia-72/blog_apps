"""
apps/contact/serializers.py
"""

from rest_framework import serializers
from .models import ContactMessage


class ContactFormSerializer(serializers.Serializer):
    """
    Validates contact form input.
    Uses plain Serializer (not ModelSerializer) so we can add
    a honeypot field for bot detection without it hitting the DB.
    """

    name = serializers.CharField(max_length=100, min_length=2)
    email = serializers.EmailField()
    subject = serializers.CharField(max_length=200, required=False, default="")
    message = serializers.CharField(min_length=20, max_length=5000)
    company = serializers.CharField(max_length=100, required=False, default="")
    budget = serializers.CharField(max_length=50, required=False, default="")
    project_type = serializers.CharField(max_length=100, required=False, default="")

    # Honeypot: hidden from real users via CSS, bots fill it automatically.
    # If this field has any value → reject the request silently.
    website_url = serializers.CharField(required=False, default="", allow_blank=True)

    def validate_website_url(self, value):
        if value:  # Bots fill hidden fields — humans never see it
            raise serializers.ValidationError("Bot detected.")
        return value

    def validate_email(self, value):
        return value.lower().strip()


class ContactMessageAdminSerializer(serializers.ModelSerializer):
    """Full message data for admin viewing and updating."""

    class Meta:
        model = ContactMessage
        fields = "__all__"
        read_only_fields = [
            "submitted_at",
            "name",
            "email",
            "message",
            "company",
            "budget",
            "project_type",
            "utm_source",
        ]

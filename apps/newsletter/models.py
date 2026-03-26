"""
apps/newsletter/models.py
==========================
Email newsletter subscriber model.
Uses double opt-in: subscriber confirms via email before going active.

Why double opt-in?
  → Better deliverability (confirmed emails = real people)
  → Required by law in EU (GDPR), recommended globally
  → Lower spam complaint rate
"""

from django.db import models


class Subscriber(models.Model):
    STATUS_CHOICES = [
        ("pending", "Pending Confirmation"),  # Signed up, not yet confirmed
        ("active", "Active"),  # Confirmed, receiving emails
        ("inactive", "Unsubscribed"),  # Opted out
    ]

    email = models.EmailField(unique=True, db_index=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="pending")

    # Where they subscribed — for analytics and A/B testing
    # Values: 'homepage', 'blog-post', 'popup', 'footer', etc.
    source = models.CharField(max_length=100, blank=True)

    subscribed_at = models.DateTimeField(auto_now_add=True)
    confirmed_at = models.DateTimeField(null=True, blank=True)
    unsubscribed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "subscribers"
        ordering = ["-subscribed_at"]

    def __str__(self):
        return f"{self.email} ({self.status})"

    @property
    def is_active(self):
        return self.status == "active"

"""
apps/contact/models.py
=======================
Contact form — your lead management inbox.
Every message goes through a mini pipeline: new → read → replied.
"""

from django.db import models


class ContactMessage(models.Model):
    STATUS_CHOICES = [
        ("new", "New"),
        ("read", "Read"),
        ("replied", "Replied"),
        ("archived", "Archived"),
    ]

    # Contact details
    name = models.CharField(max_length=100)
    email = models.EmailField(db_index=True)
    subject = models.CharField(max_length=200, blank=True)
    message = models.TextField()

    # Optional project context — helps you respond with a better proposal
    company = models.CharField(max_length=100, blank=True)
    budget = models.CharField(
        max_length=50, blank=True, help_text='e.g. $1,000–$5,000 or "Open to discuss"'
    )
    project_type = models.CharField(
        max_length=100,
        blank=True,
        help_text="Backend API, System Design, Automation, etc.",
    )

    # Pipeline tracking
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="new")
    admin_notes = models.TextField(
        blank=True, help_text="Private notes — not visible to sender."
    )

    # UTM source if they came from a campaign
    utm_source = models.CharField(max_length=100, blank=True)

    submitted_at = models.DateTimeField(auto_now_add=True)
    replied_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "contact_messages"
        ordering = ["-submitted_at"]

    def __str__(self):
        return f'{self.name} — {self.subject or "No subject"} [{self.status}]'

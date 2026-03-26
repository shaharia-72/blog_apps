"""
apps/users/models.py
====================
Custom User model extending Django's AbstractUser.
"""

from django.db import models
from django.contrib.auth.models import AbstractUser
from imagekit.models import ProcessedImageField
from imagekit.processors import ResizeToFill


class User(AbstractUser):
    """
    Extended user model with profile fields.
    Used for blog authors and admin users.
    """

    bio = models.TextField(blank=True, help_text="Author bio shown on blog posts")

    avatar = ProcessedImageField(
        upload_to="avatars/",
        processors=[ResizeToFill(200, 200)],
        format="JPEG",
        options={"quality": 85},
        default="avatars/default.jpg",
        blank=True,
        null=True,
        help_text="Profile picture (auto-resized to 200x200)",
    )

    # Social links
    website = models.URLField(blank=True, help_text="Personal website or portfolio")
    twitter_username = models.CharField(
        max_length=100,
        blank=True,
        help_text="Twitter handle without @"
    )
    linkedin_username = models.CharField(
        max_length=100,
        blank=True,
        help_text="LinkedIn profile username"
    )
    github_username = models.CharField(
        max_length=100,
        blank=True,
        help_text="GitHub username"
    )

    # Skills/expertise tags (JSON array)
    skills = models.JSONField(
        default=list,
        blank=True,
        help_text='Array of skills: ["Django", "PostgreSQL", "Redis"]'
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "users"
        ordering = ['-date_joined']
        indexes = [
            models.Index(fields=['username'], name='idx_user_username'),
            models.Index(fields=['email'], name='idx_user_email'),
        ]

    def __str__(self) -> str:
        return self.get_full_name() or self.username

    @property
    def full_name(self):
        """Return full name or username as fallback."""
        return self.get_full_name() or self.username

    @property
    def github_url(self):
        """Full GitHub profile URL."""
        return (
            f"https://github.com/{self.github_username}"
            if self.github_username else ""
        )

    @property
    def linkedin_url(self):
        """Full LinkedIn profile URL."""
        return (
            f"https://linkedin.com/in/{self.linkedin_username}"
            if self.linkedin_username else ""
        )

    @property
    def twitter_url(self):
        """Full Twitter profile URL."""
        return (
            f"https://twitter.com/{self.twitter_username}"
            if self.twitter_username else ""
        )

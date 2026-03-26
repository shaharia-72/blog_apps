from django.db import models
from django.contrib.auth.models import AbstractUser
from imagekit.models import ProcessedImageField
from imagekit.processors import ResizeToFill


class User(AbstractUser):
    bio = models.TextField(blank=True)

    avatar = ProcessedImageField(
        upload_to="avatars/",
        processors=[ResizeToFill(200, 200)],
        format="JPEG",
        options={"quality": 85},
        default="avatars/default.jpg",
        blank=True,
        null=True,
    )

    website = models.URLField(blank=True)
    linkedin_username = models.CharField(max_length=100, blank=True)
    github_username = models.CharField(max_length=100, blank=True)
    skills = models.JSONField(default=list, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "users"

    def __str__(self) -> str:
        return self.get_full_name() or self.username

    @property
    def full_name(self):
        return self.get_full_name() or self.username

    @property
    def github_url(self):
        return (
            f"https://github.com/{self.github_username}" if self.github_username else ""
        )

    @property
    def linkedin_url(self):
        return (
            f"https://linkedin.com/in/{self.linkedin_username}"
            if self.linkedin_username
            else ""
        )

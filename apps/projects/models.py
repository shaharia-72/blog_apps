"""
apps/projects/models.py
========================
Portfolio project showcase model.
"""

from django.db import models
from django.utils.text import slugify
from imagekit.models import ProcessedImageField
from imagekit.processors import ResizeToFit


class Project(models.Model):
    """
    Each project showcases a system you built.
    Link to your blog post builds internal linking (huge SEO win).
    """

    CATEGORY_CHOICES = [
        ("backend", "Backend API"),
        ("automation", "Automation / n8n"),
        ("system", "System Design"),
        ("ai", "AI / ML"),
        ("tool", "Developer Tool"),
        ("other", "Other"),
    ]

    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True, blank=True)
    description = models.TextField()
    highlights = models.TextField(
        blank=True, help_text="What problem did this solve? What did you learn?"
    )
    category = models.CharField(
        max_length=20, choices=CATEGORY_CHOICES, default="backend"
    )

    thumbnail = ProcessedImageField(
        upload_to="project_thumbnails/%Y/",
        processors=[ResizeToFit(800, 500)],
        format="WEBP",
        options={"quality": 85},
    )
    # Array of absolute URLs: ["https://cdn.../ss1.webp", ...]
    screenshots = models.JSONField(default=list, blank=True)

    # Tech stack as JSON array: ["Django", "PostgreSQL", "Redis", "Celery"]
    tech_stack = models.JSONField(default=list)
    # Key features: ["Rate limiting", "JWT Auth", "Async email"]
    features = models.JSONField(default=list)

    github_url = models.URLField(blank=True)
    live_url = models.URLField(blank=True)
    # Link to your blog post about this project — great for SEO
    blog_url = models.URLField(
        blank=True, help_text="Link to the blog post explaining how you built this."
    )

    is_featured = models.BooleanField(default=False)
    order = models.IntegerField(default=0, help_text="Lower = shows first in list.")
    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "projects"
        ordering = ["-is_featured", "order", "-created_at"]

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title

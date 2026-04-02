"""
apps/blog/models.py
====================
Core content models:

  Category   → Backend, AI/ML, System Design, DSA, Python, GenAI, Database
  Tag        → Fine-grained labels: django, redis, llm, gpt-4, celery ...
  Blog       → The main blog post
  BlogSection → Ordered content blocks inside a post (text / image / code / ad)

Why BlogSection instead of one big textarea?
  → Insert images BETWEEN paragraphs (not just header)
  → Place AdSense ads between specific sections (earns money)
  → Code blocks get proper language tagging for syntax highlighting
  → Reorder by drag-and-drop in admin
  → Add new section types in future (video, quiz, embed) without migrations
"""

from django.db import models
from django.db.models import Q
from django.utils.text import slugify
from django.contrib.auth import get_user_model
from django.utils import timezone
from imagekit.models import ProcessedImageField, ImageSpecField
from imagekit.processors import ResizeToFit, ResizeToFill
from core.utils import calculate_read_time

User = get_user_model()


# ── Category ──────────────────────────────────────────────────


class Category(models.Model):
    """
    Top-level topic groupings.
    Used in: nav menu, filter chips, sitemap, RSS feeds.
    """

    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(unique=True, blank=True, max_length=120)
    description = models.TextField(
        blank=True,
        help_text="Shown on category page — describe what this topic covers.",
    )
    color = models.CharField(
        max_length=7,
        default="#6366F1",
        help_text="Hex color for the category badge/chip in the UI.",
    )
    icon = models.CharField(
        max_length=10, blank=True, help_text="Emoji icon, e.g. ⚙️ 🤖 📊"
    )
    order = models.IntegerField(
        default=0, help_text="Display order in nav. Lower = first."
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "categories"
        ordering = ["order", "name"]
        verbose_name_plural = "Categories"

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

    @property
    def blog_count(self):
        return self.blogs.filter(status="published").count()


# ── Tag ───────────────────────────────────────────────────────


class Tag(models.Model):
    """Fine-grained labels. Many-to-many with Blog."""

    name = models.CharField(max_length=50, unique=True)
    slug = models.SlugField(unique=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "tags"
        ordering = ["name"]

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

    @property
    def blog_count(self):
        return self.blogs.filter(status="published").count()


# ── Blog Manager ──────────────────────────────────────────────


class BlogManager(models.Manager):
    """
    Custom queryset shortcuts so views stay clean.
    Usage: Blog.objects.published() instead of filter(status='published')
    """

    def published(self):
        """Only live posts, not future-scheduled ones."""
        return (
            self.filter(status="published", published_at__lte=timezone.now())
            .select_related("author", "category")
            .prefetch_related("tags")
        )

    def featured(self):
        """Homepage featured section, ordered by featured_order."""
        return self.published().filter(is_featured=True).order_by("featured_order")

    def by_language(self, lang: str):
        return self.published().filter(language=lang)


# ── Blog ──────────────────────────────────────────────────────


class Blog(models.Model):
    STATUS_CHOICES = [
        ("draft", "Draft"),
        ("published", "Published"),
        ("archived", "Archived"),
    ]
    LANGUAGE_CHOICES = [
        ("en", "English"),
        ("bn", "Bangla"),
    ]

    # ── Core ──────────────────────────────────────────────────
    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True, blank=True, max_length=250)
    language = models.CharField(max_length=2, choices=LANGUAGE_CHOICES, default="en")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="draft")
    excerpt = models.TextField(
        max_length=300,
        help_text="Short description for blog cards and meta description (max 300 chars).",
    )

    # ── Cover Image ───────────────────────────────────────────
    # Stored as WebP (30% smaller than JPEG, same quality)
    # Auto-generates thumbnail + OG image via imagekit
    cover_image = ProcessedImageField(
        upload_to="blog_covers/%Y/%m/",
        processors=[ResizeToFit(1920, 1080)],
        format="WEBP",
        options={"quality": 82},
        help_text="Upload 1920×1080px. Auto-converted to WebP.",
    )
    # 800×450px card thumbnail — lazy-generated on first access
    thumbnail = ImageSpecField(
        source="cover_image",
        processors=[ResizeToFill(800, 450)],
        format="WEBP",
        options={"quality": 80},
    )
    # 1200×630px Open Graph image for social sharing
    og_image = ImageSpecField(
        source="cover_image",
        processors=[ResizeToFill(1200, 630)],
        format="JPEG",
        options={"quality": 85},
    )

    # ── SEO ───────────────────────────────────────────────────
    seo_title = models.CharField(
        max_length=60,
        blank=True,
        help_text="Google shows ~60 chars. Leave blank to use post title.",
    )
    seo_description = models.CharField(
        max_length=160,
        blank=True,
        help_text="Google shows ~160 chars. Leave blank to use excerpt.",
    )
    seo_keywords = models.CharField(
        max_length=300,
        blank=True,
        help_text="Comma-separated: redis, caching, django, backend",
    )
    canonical_url = models.URLField(
        blank=True,
        help_text="If this is a republished post, put the original URL here.",
    )

    # ── Relations ─────────────────────────────────────────────
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name="blogs")
    category = models.ForeignKey(
        Category, on_delete=models.SET_NULL, related_name="blogs", null=True, blank=True
    )
    tags = models.ManyToManyField(Tag, related_name="blogs", blank=True)

    # ── Publishing ────────────────────────────────────────────
    published_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Set a future date/time to schedule publishing.",
    )
    is_featured = models.BooleanField(default=False)
    featured_order = models.IntegerField(
        default=0, help_text="Lower number = appears first in featured list."
    )

    # ── Analytics ─────────────────────────────────────────────
    views = models.PositiveIntegerField(default=0)
    read_time = models.PositiveSmallIntegerField(
        default=1, help_text="Auto-calculated from content length (minutes)."
    )

    # ── Timestamps ────────────────────────────────────────────
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = BlogManager()

    class Meta:
        db_table = "blogs"
        ordering = ["-published_at", "-created_at"]
        indexes = [
            # Most common query: published posts by date
            models.Index(
                fields=["status", "published_at"], name="idx_blog_status_date"
            ),
            # Language filtering: English or Bangla
            models.Index(fields=["language", "status"], name="idx_blog_language"),
            # Slug lookup for detail page
            models.Index(fields=["slug"], name="idx_blog_slug"),
            # Homepage featured section
            models.Index(fields=["is_featured", "status"], name="idx_blog_featured"),
        ]

    def save(self, *args, **kwargs):
        # Auto-generate slug from title on first save
        if not self.slug:
            self.slug = slugify(self.title)

        # Auto-fill SEO fields if blank
        if not self.seo_title:
            self.seo_title = self.title[:60]
        if not self.seo_description:
            self.seo_description = self.excerpt[:160]

        # Auto-set published_at when first published
        if self.status == "published" and not self.published_at:
            self.published_at = timezone.now()

        # Auto-calculate read time from markdown sections
        # ONLY on full saves — skip when update_fields is specified
        # (e.g., view count sync, status change) to avoid N+1 queries
        update_fields = kwargs.get('update_fields')
        if self.pk and update_fields is None:
            text = " ".join(
                s.content
                for s in self.sections.filter(section_type="markdown")
                if s.content
            )
            if text:
                self.read_time = calculate_read_time(text)

        super().save(*args, **kwargs)

    def __str__(self):
        return f"[{self.status.upper()}] {self.title}"

    def get_absolute_url(self):
        """Used by sitemap and Django admin "View on site" button."""
        return f"/blog/{self.slug}/"


# ── BlogSection ───────────────────────────────────────────────


class BlogSection(models.Model):
    """
    One ordered content block inside a blog post.

    Example layout for a tutorial post:
      order=0  type=markdown  → Introduction
      order=1  type=image     → Architecture diagram
      order=2  type=markdown  → Step-by-step explanation
      order=3  type=code      → Python code snippet
      order=4  type=ad        → AdSense between sections (money!)
      order=5  type=markdown  → Conclusion
      order=6  type=callout   → "💡 Pro tip: ..."
    """

    SECTION_TYPES = [
        ("markdown", "Markdown Text"),
        ("image", "Image Block"),
        ("code", "Code Block"),
        ("ad", "Advertisement"),
        ("callout", "Callout / Note"),
        ("divider", "Section Divider"),
    ]

    blog = models.ForeignKey(Blog, on_delete=models.CASCADE, related_name="sections")
    section_type = models.CharField(
        max_length=20, choices=SECTION_TYPES, default="markdown"
    )
    order = models.PositiveSmallIntegerField(
        default=0, help_text="Lower = appears earlier. Drag to reorder in admin."
    )

    # ── markdown fields ───────────────────────────────────────
    content = models.TextField(
        blank=True,
        help_text="Markdown content. Use # headings, ```python code blocks, | tables |.",
    )

    # ── image fields ─────────────────────────────────────────
    image = ProcessedImageField(
        upload_to="blog_sections/%Y/%m/",
        processors=[ResizeToFit(1200, 900)],
        format="WEBP",
        options={"quality": 85},
        null=True,
        blank=True,
    )
    image_caption = models.CharField(max_length=300, blank=True)
    image_alt = models.CharField(
        max_length=200,
        blank=True,
        help_text="Alt text for accessibility and SEO image indexing.",
    )

    # ── code fields ───────────────────────────────────────────
    code_language = models.CharField(
        max_length=30, blank=True, help_text="python, javascript, sql, bash, go, etc."
    )
    code_filename = models.CharField(
        max_length=100,
        blank=True,
        help_text="Optional filename shown above the code block.",
    )

    # ── ad fields ─────────────────────────────────────────────
    ad_type = models.CharField(
        max_length=20,
        blank=True,
        choices=[
            ("adsense", "Google AdSense"),
            ("affiliate", "Affiliate"),
            ("custom", "Custom HTML"),
        ],
    )
    ad_slot_id = models.CharField(
        max_length=100, blank=True, help_text="Google AdSense data-ad-slot value."
    )
    ad_custom_html = models.TextField(
        blank=True, help_text="Custom ad HTML (affiliate banners, etc.)."
    )

    # ── callout fields ────────────────────────────────────────
    callout_type = models.CharField(
        max_length=10,
        blank=True,
        choices=[
            ("info", "ℹ️ Info"),
            ("tip", "💡 Tip"),
            ("warning", "⚠️ Warning"),
            ("danger", "🚨 Danger"),
        ],
    )

    class Meta:
        db_table = "blog_sections"
        ordering = ["order"]  # Always returned in correct order

    def __str__(self):
        return f"{self.blog.slug} | §{self.order} ({self.section_type})"

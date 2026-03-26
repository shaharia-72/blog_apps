"""
apps/blog/serializers.py
=========================
Two-tier serializer strategy:
  List serializer  → lightweight, only fields needed for cards
  Detail serializer → full data including sections, SEO, related posts
"""

from rest_framework import serializers
from django.conf import settings
from django.db import models

from .models import Blog, BlogSection, Category, Tag
from apps.users.serializers import AuthorSerializer
from core.utils import markdown_to_html, build_seo_meta


# ── Category ──────────────────────────────────────────────────


class CategoryListSerializer(serializers.ModelSerializer):
    blog_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Category
        fields = ["id", "name", "slug", "color", "icon", "blog_count"]


class CategoryDetailSerializer(serializers.ModelSerializer):
    blog_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Category
        fields = ["id", "name", "slug", "description", "color", "icon", "blog_count"]


# ── Tag ───────────────────────────────────────────────────────


class TagSerializer(serializers.ModelSerializer):
    blog_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Tag
        fields = ["id", "name", "slug", "blog_count"]


# ── BlogSection ───────────────────────────────────────────────


class BlogSectionReadSerializer(serializers.ModelSerializer):
    """
    Read-only section serializer for public API responses.
    Converts Markdown → HTML server-side so the frontend
    doesn't need a Markdown parser library.
    """

    content_html = serializers.SerializerMethodField()
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = BlogSection
        fields = [
            "id",
            "section_type",
            "order",
            "content",
            "content_html",
            "image_url",
            "image_caption",
            "image_alt",
            "code_language",
            "code_filename",
            "ad_type",
            "ad_slot_id",
            "ad_custom_html",
            "callout_type",
        ]

    def get_content_html(self, obj):
        if obj.section_type == "markdown" and obj.content:
            return markdown_to_html(obj.content)
        return None

    def get_image_url(self, obj):
        if not obj.image:
            return None
        request = self.context.get("request")
        return request.build_absolute_uri(obj.image.url) if request else obj.image.url


class BlogSectionWriteSerializer(serializers.ModelSerializer):
    """Write serializer — accepts all editable section fields."""

    class Meta:
        model = BlogSection
        fields = [
            "id",
            "section_type",
            "order",
            "content",
            "image",
            "image_caption",
            "image_alt",
            "code_language",
            "code_filename",
            "ad_type",
            "ad_slot_id",
            "ad_custom_html",
            "callout_type",
        ]


# ── Blog List (lightweight for cards) ────────────────────────


class BlogListSerializer(serializers.ModelSerializer):
    """
    Used on: homepage, blog list, search results, related posts.
    Light — only fields the card UI needs. No sections, no SEO.
    """

    category = CategoryListSerializer(read_only=True)
    tags = TagSerializer(many=True, read_only=True)
    author = AuthorSerializer(read_only=True)
    cover_url = serializers.SerializerMethodField()
    thumb_url = serializers.SerializerMethodField()

    class Meta:
        model = Blog
        fields = [
            "id",
            "title",
            "slug",
            "language",
            "excerpt",
            "cover_url",
            "thumb_url",
            "category",
            "tags",
            "author",
            "published_at",
            "read_time",
            "views",
            "is_featured",
        ]

    def get_cover_url(self, obj):
        request = self.context.get("request")
        if obj.cover_image and request:
            return request.build_absolute_uri(obj.cover_image.url)
        return None

    def get_thumb_url(self, obj):
        try:
            request = self.context.get("request")
            url = obj.thumbnail.url
            return request.build_absolute_uri(url) if request else url
        except Exception:
            return self.get_cover_url(obj)


# ── Blog Detail (full data for single post page) ─────────────


class BlogDetailSerializer(serializers.ModelSerializer):
    """
    Used on: single blog post page /blog/[slug]
    Includes all sections, related posts, full author, and SEO meta block.
    The SEO meta block is consumed by Next.js to set <head> tags.
    """

    category = CategoryDetailSerializer(read_only=True)
    tags = TagSerializer(many=True, read_only=True)
    author = AuthorSerializer(read_only=True)
    sections = BlogSectionReadSerializer(many=True, read_only=True)
    related_posts = serializers.SerializerMethodField()
    cover_url = serializers.SerializerMethodField()
    og_image_url = serializers.SerializerMethodField()
    seo = serializers.SerializerMethodField()

    class Meta:
        model = Blog
        fields = [
            "id",
            "title",
            "slug",
            "language",
            "status",
            "excerpt",
            "cover_url",
            "og_image_url",
            "category",
            "tags",
            "author",
            "sections",
            "published_at",
            "updated_at",
            "read_time",
            "views",
            "is_featured",
            "seo",
            "related_posts",
        ]

    def get_cover_url(self, obj):
        request = self.context.get("request")
        if obj.cover_image and request:
            return request.build_absolute_uri(obj.cover_image.url)
        return None

    def get_og_image_url(self, obj):
        """1200×630px for social sharing (Open Graph standard)."""
        try:
            request = self.context.get("request")
            url = obj.og_image.url
            return request.build_absolute_uri(url) if request else url
        except Exception:
            return self.get_cover_url(obj)

    def get_seo(self, obj):
        """
        Build the full SEO meta block.
        Next.js reads this and populates all <head> tags:
          <title>, <meta description>, canonical, og:*, twitter:*
        Also includes JSON-LD Schema.org structured data for
        Google rich results (article cards in search).
        """
        og_image = self.get_og_image_url(obj)
        seo_meta = build_seo_meta(
            title=obj.seo_title or obj.title,
            description=obj.seo_description or obj.excerpt,
            url=obj.get_absolute_url(),
            image=og_image,
            keywords=obj.seo_keywords,
        )
        # Add article-specific JSON-LD fields
        seo_meta["schema_org"].update(
            {
                "datePublished": (
                    obj.published_at.isoformat() if obj.published_at else ""
                ),
                "dateModified": obj.updated_at.isoformat(),
                "author": {
                    "@type": "Person",
                    "name": obj.author.get_full_name() or obj.author.username,
                },
                "articleSection": obj.category.name if obj.category else "",
                "keywords": obj.seo_keywords,
                "timeRequired": f"PT{obj.read_time}M",  # ISO 8601 duration
                "wordCount": sum(
                    len(s.content.split())
                    for s in obj.sections.all()
                    if s.section_type == "markdown" and s.content
                ),
            }
        )
        return seo_meta

    def get_related_posts(self, obj):
        """
        Find related posts:
        1. Same category + overlapping tags (most relevant)
        2. Fallback to recent posts from same category
        Returns max RELATED_POSTS_COUNT (default 3).
        """
        count = settings.BLOG_SETTINGS.get("RELATED_POSTS_COUNT", 3)
        tag_ids = obj.tags.values_list("id", flat=True)

        related = list(
            Blog.objects.published()
            .exclude(id=obj.id)
            .filter(category=obj.category)
            .annotate(shared=models.Count("tags", filter=models.Q(tags__in=tag_ids)))
            .order_by("-shared", "-published_at")[:count]
        )

        if len(related) < count:
            related = list(
                Blog.objects.published()
                .exclude(id=obj.id)
                .order_by("-published_at")[:count]
            )

        return BlogListSerializer(related, many=True, context=self.context).data


# ── Admin Write Serializers ───────────────────────────────────


class BlogWriteSerializer(serializers.ModelSerializer):
    """
    Admin: create and update blog posts.
    Handles nested sections in a single request.
    """

    sections = BlogSectionWriteSerializer(many=True, required=False)
    tag_ids = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(),
        many=True,
        write_only=True,
        source="tags",
        required=False,
    )
    category_id = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.all(),
        write_only=True,
        source="category",
        required=False,
        allow_null=True,
    )

    class Meta:
        model = Blog
        fields = [
            "id",
            "title",
            "slug",
            "language",
            "status",
            "excerpt",
            "cover_image",
            "category_id",
            "tag_ids",
            "is_featured",
            "featured_order",
            "seo_title",
            "seo_description",
            "seo_keywords",
            "canonical_url",
            "published_at",
            "sections",
        ]
        read_only_fields = ["id", "slug"]

    def create(self, validated_data):
        sections_data = validated_data.pop("sections", [])
        validated_data["author"] = self.context["request"].user
        blog = Blog.objects.create(**validated_data)
        for i, sec in enumerate(sections_data):
            sec.setdefault("order", i)
            BlogSection.objects.create(blog=blog, **sec)
        return blog

    def update(self, instance, validated_data):
        sections_data = validated_data.pop("sections", None)
        for attr, val in validated_data.items():
            setattr(instance, attr, val)
        instance.save()
        if sections_data is not None:
            # Replace all sections (delete old, create new)
            instance.sections.all().delete()
            for i, sec in enumerate(sections_data):
                sec.setdefault("order", i)
                BlogSection.objects.create(blog=instance, **sec)
        return instance

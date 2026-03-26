"""
core/utils.py
==============
Shared utility functions used across all apps.
Import like: from core.utils import hash_ip, markdown_to_html
"""

import hashlib
import markdown
import bleach
import logging
from django.conf import settings
from django.core.cache import cache
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadSignature

logger = logging.getLogger(__name__)


# ── IP Hashing ────────────────────────────────────────────────


def hash_ip(ip_address: str) -> str:
    """
    Hash IP + today's date → daily-unique anonymous identifier.

    Why daily salt?
    → Can deduplicate "already viewed today?" without storing real IPs.
    → Salt rotates daily — same IP cannot be tracked across days.
    → GDPR compliant: no personal data stored ever.

    Algorithm: SHA-256(ip + YYYY-MM-DD)
    """
    from datetime import date

    raw = f"{ip_address}{date.today()}"
    return hashlib.sha256(raw.encode()).hexdigest()


def get_client_ip(request) -> str:
    """
    Extract real IP from request, even behind nginx/load balancer.
    nginx sets X-Forwarded-For: client_ip, proxy1, proxy2
    We take the leftmost = actual client.
    """
    forwarded = request.META.get("HTTP_X_FORWARDED_FOR")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR", "127.0.0.1")


# ── Read Time ─────────────────────────────────────────────────


def calculate_read_time(content: str) -> int:
    """
    Estimate reading time in minutes.
    200 WPM = average adult. Minimum: 1 min.
    1,000 words → 5 min read.
    """
    wpm = settings.BLOG_SETTINGS.get("READING_SPEED_WPM", 200)
    return max(1, round(len(content.split()) / wpm))


# ── Markdown → Safe HTML ──────────────────────────────────────


def markdown_to_html(content: str) -> str:
    """
    Convert Markdown → sanitized HTML.

    Pipeline:
      Markdown text
        → python-markdown (parses into raw HTML)
        → bleach.clean() (strips scripts, onclick, iframes, etc.)
        → safe HTML returned to frontend

    Supports: fenced code blocks, tables, TOC, syntax highlighting,
              footnotes, smart quotes, {.class} attributes.
    """
    md = markdown.Markdown(
        extensions=[
            "markdown.extensions.fenced_code",
            "markdown.extensions.tables",
            "markdown.extensions.toc",
            "markdown.extensions.codehilite",
            "markdown.extensions.nl2br",
            "markdown.extensions.attr_list",
            "markdown.extensions.footnotes",
            "markdown.extensions.smarty",
            "markdown.extensions.sane_lists",
            "markdown.extensions.meta",  # Front matter: Title: ..., Date: ...
        ]
    )
    raw = md.convert(content)

    ALLOWED_TAGS = [
        "h1",
        "h2",
        "h3",
        "h4",
        "h5",
        "h6",
        "p",
        "br",
        "hr",
        "div",
        "span",
        "strong",
        "em",
        "b",
        "i",
        "u",
        "s",
        "del",
        "ins",
        "mark",
        "small",
        "sup",
        "sub",
        "ul",
        "ol",
        "li",
        "dl",
        "dt",
        "dd",
        "pre",
        "code",
        "kbd",
        "samp",
        "a",
        "img",
        "figure",
        "figcaption",
        "blockquote",
        "cite",
        "q",
        "table",
        "thead",
        "tbody",
        "tfoot",
        "tr",
        "th",
        "td",
        "caption",
        "abbr",
        "details",
        "summary",
    ]
    ALLOWED_ATTRS = {
        "*": ["class", "id"],
        "a": ["href", "title", "rel", "target"],
        "img": ["src", "alt", "title", "width", "height", "loading", "decoding"],
        "code": ["class"],
        "pre": ["class"],
        "th": ["align", "scope"],
        "td": ["align"],
        "abbr": ["title"],
    }

    return bleach.clean(raw, tags=ALLOWED_TAGS, attributes=ALLOWED_ATTRS, strip=True)


# ── Cache Helpers ─────────────────────────────────────────────


def get_or_set_cache(key: str, callback, timeout: int = None):
    """
    Cache-aside pattern.
    Reads from Redis first; on miss runs callback() and caches the result.
    """
    result = cache.get(key)
    if result is not None:
        return result
    result = callback()
    cache.set(key, result, timeout)
    return result


def invalidate_blog_cache(slug: str = None):
    """
    Bust all blog-related cache after content changes.
    django-redis supports wildcard delete_pattern().
    """
    patterns = ["blog:list:*", "blog:featured", "analytics:public_stats", "blog:rss:*"]
    if slug:
        patterns += [f"blog:detail:{slug}", f"blog:stats:{slug}"]
    for p in patterns:
        try:
            cache.delete_pattern(p)
        except Exception:
            # Fallback if delete_pattern not available
            cache.delete(p.replace(":*", ""))


# ── Email Tokens (itsdangerous) ───────────────────────────────


def _get_signer():
    return URLSafeTimedSerializer(settings.SECRET_KEY, salt="newsletter-confirm-v1")


def generate_confirm_token(email: str) -> str:
    """
    Create a signed, time-limited token for email confirmation.
    Expires after settings.EMAIL_CONFIRM_TOKEN_EXPIRY seconds (24h default).
    Safe against tampering because it's signed with SECRET_KEY.
    """
    return _get_signer().dumps(email.lower().strip())


def verify_confirm_token(token: str) -> str | None:
    """
    Decode and verify email confirmation token.
    Returns email if valid, None if expired or tampered.
    """
    max_age = getattr(settings, "EMAIL_CONFIRM_TOKEN_EXPIRY", 86400)
    try:
        return _get_signer().loads(token, max_age=max_age)
    except SignatureExpired:
        logger.info("Expired email confirmation token used")
        return None
    except BadSignature:
        logger.warning("Invalid/tampered email confirmation token rejected")
        return None


# ── SEO Helpers ───────────────────────────────────────────────


def build_seo_meta(
    title: str, description: str, url: str, image: str = None, keywords: str = ""
) -> dict:
    """
    Build a structured SEO meta dict for API responses.
    Next.js frontend uses this to populate <head> meta tags.

    Covers: standard meta, Open Graph (Facebook/LinkedIn), Twitter Card.
    """
    seo = settings.SEO_SETTINGS
    full_title = f'{title} | {seo["SITE_NAME"]}' if title else seo["DEFAULT_TITLE"]
    desc = description or seo["DEFAULT_DESCRIPTION"]
    full_url = f'{seo["SITE_URL"]}{url}'

    return {
        # Standard HTML meta
        "title": full_title,
        "description": desc[:160],
        "keywords": keywords,
        "canonical": full_url,
        # Open Graph (Facebook, LinkedIn, WhatsApp previews)
        "og": {
            "title": full_title,
            "description": desc[:200],
            "url": full_url,
            "type": "article",
            "image": image or "",
            "site_name": seo["SITE_NAME"],
        },
        # Twitter Card
        "twitter": {
            "card": "summary_large_image",
            "title": full_title[:70],
            "description": desc[:200],
            "image": image or "",
            "creator": seo.get("TWITTER_HANDLE", ""),
        },
        # JSON-LD structured data for Google rich results
        "schema_org": {
            "@context": "https://schema.org",
            "@type": seo.get("SCHEMA_ORG_TYPE", "BlogPosting"),
            "headline": title[:110],
            "description": desc[:300],
            "url": full_url,
            "image": image or "",
            "publisher": {
                "@type": "Organization",
                "name": seo["SITE_NAME"],
                "url": seo["SITE_URL"],
            },
        },
    }

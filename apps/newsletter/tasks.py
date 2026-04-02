"""
apps/newsletter/tasks.py
=========================
Celery tasks: confirmation email, weekly digest, cleanup.
"""

from celery import shared_task
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, queue="email", default_retry_delay=60)
def send_confirmation_email(self, email: str, token: str):
    """
    Send the double opt-in confirmation email.
    The confirm link is signed and expires in 24h.
    If sending fails, retries up to 3 times with 60s delay.
    """
    confirm_url = f"{settings.FRONTEND_URL}/newsletter/confirm/{token}/"

    try:
        # Plain text fallback for clients that block HTML
        text_body = (
            f"Hi,\n\nConfirm your subscription to "
            f"{settings.SEO_SETTINGS['SITE_NAME']} here:\n\n"
            f"{confirm_url}\n\n"
            f"This link expires in 24 hours.\n\n"
            f"If you didn't subscribe, ignore this email."
        )

        # HTML email — rendered from template
        try:
            html_body = render_to_string(
                "emails/newsletter_confirm.html",
                {
                    "confirm_url": confirm_url,
                    "site_name": settings.SEO_SETTINGS["SITE_NAME"],
                    "frontend_url": settings.FRONTEND_URL,
                },
            )
        except Exception:
            html_body = None  # Template not found — use text only

        msg = EmailMultiAlternatives(
            subject=f"Confirm your subscription to {settings.SEO_SETTINGS['SITE_NAME']} 📧",
            body=text_body,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[email],
        )
        if html_body:
            msg.attach_alternative(html_body, "text/html")
        msg.send()

        logger.info(f"Confirmation email sent to {email}")

    except Exception as exc:
        logger.error(f"Failed to send confirmation email to {email}: {exc}")
        raise self.retry(exc=exc)


@shared_task(queue="email")
def send_weekly_digest():
    """
    Send weekly new-posts digest to all active subscribers.
    Scheduled every Monday at 9am via celery beat.

    FIX H4: Uses iterator() to stream subscribers from DB instead of
    loading all into memory at once. Prevents OOM with large lists.
    """
    from apps.blog.models import Blog
    from .models import Subscriber
    from django.utils import timezone
    from datetime import timedelta

    week_ago = timezone.now() - timedelta(days=7)
    new_posts = (
        Blog.objects.filter(status="published", published_at__gte=week_ago)
        .select_related("category")
        .order_by("-published_at")[:5]
    )

    if not new_posts.exists():
        logger.info("No new posts this week — skipping newsletter digest")
        return

    # Build email body once (shared across all batches)
    post_lines = "\n".join(
        f"  • {p.title} ({p.read_time} min read)\n"
        f"    {settings.SEO_SETTINGS['SITE_URL']}/blog/{p.slug}/"
        for p in new_posts
    )
    text_body = (
        f"Here's what's new on {settings.SEO_SETTINGS['SITE_NAME']} this week:\n\n"
        f"{post_lines}\n\n"
        f"Visit the blog: {settings.FRONTEND_URL}/blog/\n\n"
        f"Unsubscribe: {settings.FRONTEND_URL}/newsletter/unsubscribe/"
    )

    try:
        html_body = render_to_string(
            "emails/weekly_digest.html",
            {
                "posts": new_posts,
                "site_name": settings.SEO_SETTINGS["SITE_NAME"],
                "frontend_url": settings.FRONTEND_URL,
            },
        )
    except Exception:
        html_body = None

    # Stream subscribers and send in batches of 100 — never loads all into memory
    batch = []
    total_sent = 0
    subscriber_qs = Subscriber.objects.filter(status="active").values_list("email", flat=True)

    for email in subscriber_qs.iterator(chunk_size=100):
        batch.append(email)
        if len(batch) >= 100:
            _send_digest_batch(batch, text_body, html_body, new_posts)
            total_sent += len(batch)
            batch = []

    # Send remaining
    if batch:
        _send_digest_batch(batch, text_body, html_body, new_posts)
        total_sent += len(batch)

    logger.info(f"Weekly digest sent to {total_sent} subscribers")


def _send_digest_batch(emails, text_body, html_body, new_posts):
    """Send digest email to a batch of subscribers via BCC."""
    msg = EmailMultiAlternatives(
        subject=f"📰 New on {settings.SEO_SETTINGS['SITE_NAME']} — {new_posts.count()} posts this week",
        body=text_body,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[settings.DEFAULT_FROM_EMAIL],  # "to" yourself
        bcc=list(emails),  # BCC subscribers (privacy)
    )
    if html_body:
        msg.attach_alternative(html_body, "text/html")
    msg.send()


@shared_task(queue="email")
def cleanup_unconfirmed():
    """
    Delete pending subscribers older than 30 days.
    Runs daily via celery beat. Keeps the DB clean.
    """
    from .models import Subscriber
    from django.utils import timezone
    from datetime import timedelta

    cutoff = timezone.now() - timedelta(days=30)
    count, _ = Subscriber.objects.filter(
        status="pending", subscribed_at__lt=cutoff
    ).delete()

    logger.info(f"Deleted {count} unconfirmed subscribers older than 30 days")

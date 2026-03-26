"""
apps/contact/tasks.py
======================
Celery task: notify admin of new contact form submission.
"""

from celery import shared_task
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, queue="email", default_retry_delay=60)
def notify_admin_new_contact(self, message_id: int):
    """
    Email the admin when a new contact form is submitted.
    Runs async via Celery — user gets instant 201 response,
    admin email arrives a few seconds later.
    """
    try:
        from .models import ContactMessage

        msg = ContactMessage.objects.get(id=message_id)

        subject = f"📬 New Contact: {msg.name}"
        if msg.subject:
            subject += f" — {msg.subject}"

        text_body = (
            f"New contact from {msg.name} <{msg.email}>\n\n"
            f"Subject: {msg.subject or 'N/A'}\n"
            f"Company: {msg.company or 'N/A'}\n"
            f"Budget:  {msg.budget or 'N/A'}\n"
            f"Type:    {msg.project_type or 'N/A'}\n\n"
            f"Message:\n{msg.message}\n\n"
            f"Reply at: {settings.FRONTEND_URL}/admin/contact/{msg.id}/"
        )

        try:
            html_body = render_to_string(
                "emails/new_contact.html",
                {
                    "msg": msg,
                    "admin_url": f"{settings.FRONTEND_URL}/admin/contact/{msg.id}/",
                    "site_name": settings.SEO_SETTINGS["SITE_NAME"],
                },
            )
        except Exception:
            html_body = None

        email = EmailMultiAlternatives(
            subject=subject,
            body=text_body,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[settings.ADMIN_EMAIL],
        )
        if html_body:
            email.attach_alternative(html_body, "text/html")
        email.send()

        logger.info(f"Contact notification sent for message {message_id}")

    except Exception as exc:
        logger.error(f"notify_admin_new_contact failed for id={message_id}: {exc}")
        raise self.retry(exc=exc)

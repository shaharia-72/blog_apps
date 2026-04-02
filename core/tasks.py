"""
core/tasks.py
==============
Scheduled maintenance tasks for the blog backend.
"""

import os
import subprocess
from datetime import datetime
from django.core.mail import EmailMessage
from django.conf import settings
from celery import shared_task
import logging

logger = logging.getLogger(__name__)


@shared_task(name="core.tasks.backup_database_to_email")
def backup_database_to_email():
    """
    Perform pg_dump of the database and email it to ADMIN_EMAIL.
    Suggested schedule: Weekly.
    """
    if not settings.USE_POSTGRES:
        logger.warning("SKIP BACKUP: Only PostgreSQL backups are supported.")
        return

    admin_email = getattr(settings, "ADMIN_EMAIL", None)
    if not admin_email:
        logger.error("SKIP BACKUP: ADMIN_EMAIL not configured.")
        return

    # 1. Prepare filename and path
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M")
    filename = f"blog_backup_{timestamp}.sql"
    filepath = f"/tmp/{filename}"

    try:
        # 2. Run pg_dump
        # DATABASE_URL is already in the environment
        db_url = os.getenv("DATABASE_URL")
        logger.info(f"Starting database backup: {filename}")
        
        # Note: pg_dump must be installed for this to work
        subprocess.run(
            ["pg_dump", db_url, "-f", filepath, "-F", "p"],
            check=True,
            capture_output=True,
            text=True
        )

        # 3. Email the file
        email = EmailMessage(
            subject=f"📦 Weekly DB Backup: {timestamp}",
            body=f"Attached is the weekly database backup for {settings.SITE_NAME}.",
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[admin_email],
        )
        email.attach_file(filepath)
        email.send()

        logger.info(f"Backup successful and sent to {admin_email}")

    except subprocess.CalledProcessError as e:
        logger.error(f"BACKUP FAILED (pg_dump): {e.stderr}")
    except Exception as e:
        logger.error(f"BACKUP FAILED: {str(e)}")
    finally:
        # 4. Cleanup
        if os.path.exists(filepath):
            os.remove(filepath)

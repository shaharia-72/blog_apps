#!/usr/bin/env bash

# Start Gunicorn (Django Web Server) in the background
gunicorn config.wsgi:application --bind 0.0.0.0:$PORT --workers 2 &

# Start Celery Worker in the background
# We use --concurrency=1 to save RAM (Render Free Tier only gives 512MB)
celery -A config worker --concurrency=1 -l info -Q default,email,analytics &

# Start Celery Beat in the background
celery -A config beat -l info --scheduler django_celery_beat.schedulers:DatabaseScheduler &

# Wait for any process to exit so the container doesn't crash prematurely
wait -n

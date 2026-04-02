#!/usr/bin/env bash

# Start Gunicorn (Django Web Server) - Reduced to 1 worker for RAM saving
# --max-requests restarts the worker after 500 requests to clear memory leaks
gunicorn config.wsgi:application \
    --bind 0.0.0.0:$PORT \
    --workers 1 \
    --threads 2 \
    --max-requests 500 \
    --max-requests-jitter 50 \
    --log-level info &

# Start Celery Worker
# --max-tasks-per-child=10 ensures the process restarts after 10 tasks to free up RAM
celery -A config worker \
    --concurrency=1 \
    --max-tasks-per-child=10 \
    -l info \
    -Q default,email,analytics &

# Start Celery Beat
celery -A config beat -l info --scheduler django_celery_beat.schedulers:DatabaseScheduler &

# Wait for any process to exit so the container doesn't crash prematurely
wait -n

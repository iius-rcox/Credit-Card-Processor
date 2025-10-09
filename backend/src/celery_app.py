"""
Celery application for background task processing.

This module configures Celery to use Redis as the broker and result backend.
"""

from celery import Celery
from .config import settings

# Construct Redis URL for Celery
# Use database 1 to avoid conflicts with other apps using the same Redis instance
# Priority: REDIS_URL > constructed from REDIS_HOST > default cluster service
if settings.REDIS_URL:
    redis_url = settings.REDIS_URL
elif settings.REDIS_HOST:
    redis_url = f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT or 6379}/1"
else:
    # Default to cluster service in AKS
    redis_url = "redis://redis-service.safety-amp.svc.cluster.local:6379/1"

# Create Celery app
celery_app = Celery(
    "credit_card_processor",
    broker=redis_url,
    backend=redis_url,
    include=["src.tasks"]
)

# Configure Celery
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=3600,  # 1 hour max per task
    task_soft_time_limit=3300,  # 55 minute soft limit
    worker_prefetch_multiplier=1,  # Process one task at a time
    worker_max_tasks_per_child=50,  # Restart worker after 50 tasks
)

"""
Celery application for background task processing.

This module configures Celery to use Redis as the broker and result backend.
"""

import logging
from celery import Celery
from .config import settings

logger = logging.getLogger(__name__)

logger.info("=" * 80)
logger.info("CELERY APP INITIALIZATION")
logger.info("=" * 80)

# Construct Redis URL for Celery
# Use database 1 to avoid conflicts with other apps using the same Redis instance
# Priority: REDIS_URL > constructed from REDIS_HOST > default cluster service
if settings.REDIS_URL:
    redis_url = settings.REDIS_URL
    logger.info(f"  Using REDIS_URL from settings")
elif settings.REDIS_HOST:
    redis_url = f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT or 6379}/1"
    logger.info(f"  Constructed Redis URL from REDIS_HOST: {settings.REDIS_HOST}")
else:
    # Default to cluster service in AKS
    redis_url = "redis://redis-service.safety-amp.svc.cluster.local:6379/1"
    logger.info(f"  Using default cluster Redis URL")

logger.info(f"  Redis URL: {redis_url}")

# Create Celery app
logger.info(f"→ Creating Celery app...")
celery_app = Celery(
    "credit_card_processor",
    broker=redis_url,
    backend=redis_url,
    include=["src.tasks"]
)
logger.info(f"✓ Celery app created: {celery_app}")
logger.info(f"  Broker: {celery_app.conf.broker_url}")
logger.info(f"  Backend: {celery_app.conf.result_backend}")
logger.info(f"  Includes: {celery_app.conf.include}")

# Configure Celery
logger.info(f"→ Configuring Celery app...")
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
logger.info(f"✓ Celery app configured")
logger.info(f"  Task serializer: {celery_app.conf.task_serializer}")
logger.info(f"  Task track started: {celery_app.conf.task_track_started}")
logger.info(f"  Task time limit: {celery_app.conf.task_time_limit}s")
logger.info("=" * 80)

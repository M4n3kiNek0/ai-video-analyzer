"""
Celery Configuration.
"""
import os
from celery import Celery

# Get Redis URL from environment or default to localhost
msg_broker_url = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")
result_backend = os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/0")

celery_app = Celery(
    "video_analyzer",
    broker=msg_broker_url,
    backend=result_backend,
    include=["processing_pipeline"]  # Import tasks from here
)

# Optional configuration
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    worker_prefetch_multiplier=1,  # Improve reliability for long tasks
    task_acks_late=True,          # Only ack after task completion
)

if __name__ == "__main__":
    celery_app.start()

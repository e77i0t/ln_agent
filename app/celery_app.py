from celery import Celery
from config import get_config
import os

config = get_config()

# Use environment variables with fallback to config
broker_url = os.environ.get('CELERY_BROKER_URL') or config.REDIS_URL
result_backend = os.environ.get('CELERY_RESULT_BACKEND') or config.REDIS_URL

celery = Celery(
    'company_research_tool',
    broker=broker_url,
    backend=result_backend,
    include=['app.tasks']  # This will include tasks from app/tasks.py
)

# Optional configurations
celery.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    broker_connection_retry_on_startup=True,  # Add this to handle connection retries
    worker_max_tasks_per_child=50,  # Restart worker after 50 tasks
    worker_max_memory_per_child=150000,  # 150MB max memory per worker
    task_soft_time_limit=300,  # 5 minute soft timeout
    task_time_limit=600,  # 10 minute hard timeout
) 
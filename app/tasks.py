from app.celery_app import celery

@celery.task
def test_task(x, y):
    """A sample task that adds two numbers."""
    return x + y 
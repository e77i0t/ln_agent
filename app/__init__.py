from flask import Flask, jsonify
from app.utils.logger import setup_logger
from app.tasks import test_task
from celery.result import AsyncResult
from app.database.connection import DatabaseManager
import redis
import os

def check_mongodb():
    """Check MongoDB connection"""
    try:
        db_manager = DatabaseManager(os.environ.get('MONGODB_URI', 'mongodb://localhost:27017/company_research'))
        if db_manager.connect() and db_manager.health_check():
            return {"status": "healthy"}
        return {"status": "unhealthy", "message": "Failed to connect to MongoDB"}
    except Exception as e:
        return {"status": "unhealthy", "message": str(e)}
    finally:
        if db_manager:
            db_manager.disconnect()

def check_redis():
    """Check Redis connection"""
    try:
        redis_url = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')
        client = redis.from_url(redis_url)
        client.ping()
        return {"status": "healthy"}
    except Exception as e:
        return {"status": "unhealthy", "message": str(e)}

def check_celery():
    """Check Celery connection"""
    try:
        # Try to send a test task
        task = test_task.delay(2, 2)
        # Wait for a short time to see if task is received
        result = AsyncResult(task.id)
        if result.state in ['PENDING', 'STARTED', 'SUCCESS']:
            return {"status": "healthy"}
        return {"status": "unhealthy", "message": f"Task state: {result.state}"}
    except Exception as e:
        return {"status": "unhealthy", "message": str(e)}

def create_app(config_object=None):
    """
    Create and configure the Flask application.
    
    Args:
        config_object: Configuration object or string
        
    Returns:
        Flask application instance
    """
    # Force port 5280 before Flask is initialized
    os.environ['PORT'] = '5280'
    os.environ['FLASK_RUN_PORT'] = '5280'
    
    app = Flask(__name__)
    
    # Load configuration
    if config_object is None:
        # Import here to avoid circular imports
        from config import get_config
        config_object = get_config()
    app.config.from_object(config_object)
    
    # Set up logging
    setup_logger(__name__, config_object)
    
    # Force port configuration
    app.config['PORT'] = 5280
    
    # Register blueprints (to be added later)
    
    @app.route('/health')
    def health_check():
        """Basic health check endpoint."""
        return {'status': 'healthy'}, 200
    
    @app.route('/health/mongodb')
    def mongodb_health():
        """MongoDB health check endpoint."""
        status = check_mongodb()
        return status, 200 if status["status"] == "healthy" else 503
    
    @app.route('/health/redis')
    def redis_health():
        """Redis health check endpoint."""
        status = check_redis()
        return status, 200 if status["status"] == "healthy" else 503
    
    @app.route('/health/celery')
    def celery_health():
        """Celery health check endpoint."""
        status = check_celery()
        return status, 200 if status["status"] == "healthy" else 503
    
    @app.route('/health/all')
    def all_services_health():
        """Check health of all services."""
        services = {
            'api': {'status': 'healthy'},
            'mongodb': check_mongodb(),
            'redis': check_redis(),
            'celery': check_celery()
        }
        
        all_healthy = all(service['status'] == 'healthy' for service in services.values())
        response = {
            'status': 'healthy' if all_healthy else 'unhealthy',
            'services': services
        }
        
        return response, 200 if all_healthy else 503
    
    @app.route('/tasks/test', methods=['POST'])
    def trigger_test_task():
        """Trigger a test Celery task."""
        task = test_task.delay(4, 4)
        return jsonify({
            'task_id': task.id,
            'status': 'Task started'
        }), 202
    
    @app.route('/tasks/<task_id>/result')
    def get_task_result(task_id):
        """Get the result of a task by its ID."""
        result = AsyncResult(task_id)
        return jsonify({
            'task_id': task_id,
            'status': result.status,
            'result': result.result if result.ready() else None
        })
    
    return app 
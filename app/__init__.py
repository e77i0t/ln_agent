from flask import Flask, jsonify
from app.utils.logger import setup_logger
from app.tasks import test_task
from celery.result import AsyncResult
import os

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
"""
Flask application factory and configuration.
"""

from flask import Flask, jsonify
from flask_cors import CORS
from app.utils.logger import setup_logger
from app.database.connection import DatabaseManager
import redis
import os
import logging

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

def create_app(config_name='development'):
    """
    Create and configure the Flask application.
    
    Args:
        config_name: Name of the configuration to use (development, testing, production)
        
    Returns:
        Flask application instance
    """
    app = Flask(__name__)
    
    # Load configuration
    app.config.from_object(f'config.{config_name.title()}Config')
    
    # Enable CORS
    CORS(app)
    
    # Set up logging
    logging.basicConfig(level=app.config.get('LOG_LEVEL', 'INFO'))
    
    # Initialize database
    app.db = DatabaseManager(app.config['MONGODB_URI'])
    app.db.connect()
    
    # Register blueprints
    from app.api.routes import api_bp
    app.register_blueprint(api_bp, url_prefix='/api')
    
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
    
    @app.route('/health/all')
    def all_services_health():
        """Check health of all services."""
        services = {
            'api': {'status': 'healthy'},
            'mongodb': check_mongodb(),
            'redis': check_redis()
        }
        
        all_healthy = all(service['status'] == 'healthy' for service in services.values())
        response = {
            'status': 'healthy' if all_healthy else 'unhealthy',
            'services': services
        }
        
        return response, 200 if all_healthy else 503
    
    return app 
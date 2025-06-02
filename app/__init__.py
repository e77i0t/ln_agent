"""
Flask application factory and configuration.
"""

from flask import Flask, jsonify
from flask_cors import CORS
from app.utils.logger import setup_logger
from app.database.connection import DatabaseManager
from app.utils.db_init import DatabaseInitializer
import redis
import os

logger = setup_logger(__name__)

def check_mongodb():
    """Check MongoDB connection"""
    try:
        db_manager = DatabaseManager(os.environ.get('MONGODB_URI', 'mongodb://localhost:27017/company_research'))
        if db_manager.connect() and db_manager.health_check():
            return {"status": "healthy"}
        return {"status": "unhealthy", "message": "Failed to connect to MongoDB"}
    except Exception as e:
        logger.error(f"MongoDB health check failed: {str(e)}")
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
        logger.error(f"Redis health check failed: {str(e)}")
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
    app.logger = setup_logger('flask.app', app.config.get('LOG_LEVEL', 'INFO'))
    
    # Initialize database connection as a global object
    mongodb_uri = app.config.get('MONGODB_URI', 'mongodb://localhost:27017/company_research')
    app.db = DatabaseManager(mongodb_uri)
    
    # Ensure database connection and initialization
    if not app.db.connect():
        logger.error("Failed to connect to MongoDB")
        raise RuntimeError("Failed to connect to MongoDB")
        
    # Initialize database (create indexes, etc.)
    initializer = DatabaseInitializer(app.db)
    if not initializer.initialize_database():
        logger.error("Failed to initialize database")
        raise RuntimeError("Failed to initialize database")
        
    logger.info("Successfully connected to MongoDB and initialized database")
    
    # Register blueprints
    from app.api.routes import api_bp
    app.register_blueprint(api_bp, url_prefix='/api')
    
    @app.before_request
    def ensure_db_connection():
        """Ensure database connection is active before each request"""
        if not app.db.health_check():
            logger.warning("Database connection lost, attempting to reconnect...")
            if not app.db.connect():
                logger.error("Failed to reconnect to database")
                return jsonify({"error": "Database connection error"}), 503
    
    @app.teardown_appcontext
    def shutdown_session(exception=None):
        """Clean up database connection"""
        if hasattr(app, 'db'):
            app.db.disconnect()
    
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
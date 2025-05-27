from flask import Flask
from app.utils.logger import setup_logger

def create_app(config_object=None):
    """
    Create and configure the Flask application.
    
    Args:
        config_object: Configuration object or string
        
    Returns:
        Flask application instance
    """
    app = Flask(__name__)
    
    # Load configuration
    if config_object is None:
        # Import here to avoid circular imports
        from config import get_config
        config_object = get_config()
    app.config.from_object(config_object)
    
    # Set up logging
    setup_logger(__name__, config_object)
    
    # Register blueprints (to be added later)
    
    @app.route('/health')
    def health_check():
        """Basic health check endpoint."""
        return {'status': 'healthy'}, 200
    
    return app 
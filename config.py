"""
Application configuration settings.
"""

import os
from dotenv import load_dotenv
from datetime import timedelta

load_dotenv()

class BaseConfig:
    """Base configuration"""
    # Flask
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev_key_change_in_production')
    DEBUG = False
    TESTING = False
    PORT = int(os.environ.get('PORT', 5280))
    
    # MongoDB
    MONGODB_URI = os.environ.get('MONGODB_URI', 'mongodb://localhost:27017/company_research')
    
    # Redis
    REDIS_URL = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')
    
    # Logging
    LOG_LEVEL = 'INFO'
    
    # API Settings
    API_TITLE = 'Company Research API'
    API_VERSION = 'v1'
    
    # Research Settings
    MAX_CONCURRENT_SESSIONS = 5
    SESSION_TIMEOUT = timedelta(hours=1)
    MAX_RESULTS_PER_PAGE = 50

class DevelopmentConfig(BaseConfig):
    """Development configuration"""
    DEBUG = True
    LOG_LEVEL = 'DEBUG'
    
    # Development-specific settings
    MONGODB_URI = os.environ.get('MONGODB_URI', 'mongodb://localhost:27017/company_research_dev')
    REDIS_URL = os.environ.get('REDIS_URL', 'redis://localhost:6379/1')

class TestingConfig(BaseConfig):
    """Testing configuration"""
    TESTING = True
    DEBUG = True
    
    # Test database
    MONGODB_URI = os.environ.get('MONGODB_URI', 'mongodb://localhost:27017/company_research_test')
    REDIS_URL = os.environ.get('REDIS_URL', 'redis://localhost:6379/2')
    
    # Test-specific settings
    WTF_CSRF_ENABLED = False
    PRESERVE_CONTEXT_ON_EXCEPTION = False
    
    # Faster timeouts for testing
    SESSION_TIMEOUT = timedelta(minutes=5)

class ProductionConfig(BaseConfig):
    """Production configuration"""
    # Ensure debug is off in production
    DEBUG = False
    
    # Stricter settings
    SESSION_TIMEOUT = timedelta(minutes=30)
    MAX_CONCURRENT_SESSIONS = 20
    
    # Required settings that must be set in production
    def __init__(self):
        super().__init__()
        required_env_vars = [
            'SECRET_KEY',
            'MONGODB_URI',
            'REDIS_URL'
        ]
        
        missing_vars = [var for var in required_env_vars if not os.environ.get(var)]
        if missing_vars:
            raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")

# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}

def get_config():
    """Return the appropriate configuration object based on environment."""
    env = os.environ.get('FLASK_ENV', 'development')
    return config.get(env, config['default']) 
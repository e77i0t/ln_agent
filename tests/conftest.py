"""
Test configuration and fixtures.
"""

import pytest
import os
import mongomock
from app.database.connection import DatabaseManager

@pytest.fixture(scope='session', autouse=True)
def mock_mongodb():
    """Mock MongoDB for testing"""
    mongodb_client = mongomock.MongoClient()
    db = mongodb_client['test_db']
    
    # Create required collections
    db.create_collection('companies')
    db.create_collection('research_sessions')
    db.create_collection('tasks')
    
    return db

@pytest.fixture(scope='session', autouse=True)
def app_config(mock_mongodb):
    """Configure app for testing"""
    os.environ['FLASK_ENV'] = 'testing'
    os.environ['MONGODB_URI'] = 'mongodb://testdb:27017/test_db'
    
    # Mock the database manager
    def mock_connect(self):
        self.client = mock_mongodb.client
        self.db = mock_mongodb
        return True
    
    def mock_health_check(self):
        return True
    
    # Patch DatabaseManager methods
    DatabaseManager.connect = mock_connect
    DatabaseManager.health_check = mock_health_check
    
    yield
    
    # Clean up
    mock_mongodb.client.drop_database('test_db')
    os.environ.pop('FLASK_ENV', None)
    os.environ.pop('MONGODB_URI', None)

@pytest.fixture(scope='session')
def test_db(mock_mongodb):
    """Provide test database instance"""
    return mock_mongodb

@pytest.fixture
def app():
    """Create and configure a test Flask application instance."""
    app = create_app(TestingConfig)
    return app

@pytest.fixture
def client(app):
    """Create a test client for the Flask application."""
    return app.test_client()

@pytest.fixture
def runner(app):
    """Create a test CLI runner for the Flask application."""
    return app.test_cli_runner() 
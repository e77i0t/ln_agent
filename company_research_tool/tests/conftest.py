import pytest
from app import create_app
from config import TestingConfig

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
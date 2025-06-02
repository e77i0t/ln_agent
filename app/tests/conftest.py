import pytest
from app.database.connection import DatabaseManager
import os

@pytest.fixture(scope="session")
def db_manager():
    """Create a database manager instance for testing."""
    mongo_url = os.environ.get('MONGODB_URL', 'mongodb://localhost:27017/company_research_test')
    manager = DatabaseManager(mongo_url)
    if not manager.connect():
        pytest.fail("Failed to connect to test database")
    yield manager
    manager.disconnect()

@pytest.fixture(autouse=True)
def cleanup_collections(db_manager):
    """Clean up all collections after each test."""
    yield
    collections = ['companies', 'contacts', 'tasks', 'research_sessions']
    for collection in collections:
        db_manager.get_collection(collection).delete_many({}) 
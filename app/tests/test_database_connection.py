import pytest
from app.database.connection import DatabaseManager
import os
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError

def test_successful_connection():
    """Test successful database connection."""
    db_manager = DatabaseManager(os.environ.get('MONGODB_URL', 'mongodb://localhost:27017/company_research_test'))
    assert db_manager.connect() is True
    assert db_manager.client is not None
    assert db_manager.db is not None
    db_manager.disconnect()

def test_invalid_connection_string():
    """Test connection with invalid MongoDB URL."""
    db_manager = DatabaseManager('mongodb://invalid:27017/test')
    assert db_manager.connect() is False
    assert db_manager.client is None
    assert db_manager.db is None

def test_connection_timeout():
    """Test connection timeout handling."""
    # Use a non-routable IP address to force timeout
    db_manager = DatabaseManager('mongodb://240.0.0.1:27017/test')
    assert db_manager.connect() is False

def test_health_check():
    """Test database health check functionality."""
    db_manager = DatabaseManager(os.environ.get('MONGODB_URL', 'mongodb://localhost:27017/company_research_test'))
    db_manager.connect()
    assert db_manager.health_check() is True
    db_manager.disconnect()

def test_multiple_connections():
    """Test multiple connection attempts."""
    db_manager = DatabaseManager(os.environ.get('MONGODB_URL', 'mongodb://localhost:27017/company_research_test'))
    
    # First connection should succeed
    assert db_manager.connect() is True
    
    # Second connection attempt should return True (already connected)
    assert db_manager.connect() is True
    
    db_manager.disconnect()
    
    # After disconnect, should be able to connect again
    assert db_manager.connect() is True
    db_manager.disconnect()

def test_disconnect_handling():
    """Test disconnect behavior."""
    db_manager = DatabaseManager(os.environ.get('MONGODB_URL', 'mongodb://localhost:27017/company_research_test'))
    
    # Disconnect without connecting first should not raise error
    db_manager.disconnect()
    
    # Connect and disconnect
    db_manager.connect()
    db_manager.disconnect()
    
    # Verify client and db are None after disconnect
    assert db_manager.client is None
    assert db_manager.db is None

def test_get_collection():
    """Test getting collection from database."""
    db_manager = DatabaseManager(os.environ.get('MONGODB_URL', 'mongodb://localhost:27017/company_research_test'))
    db_manager.connect()
    
    # Test getting a collection
    collection = db_manager.get_collection('test_collection')
    assert collection is not None
    
    # Test getting same collection again (should use cached connection)
    collection2 = db_manager.get_collection('test_collection')
    assert collection2 is not None
    
    db_manager.disconnect() 
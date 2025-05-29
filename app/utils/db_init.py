from typing import List, Dict, Any
import logging
from pymongo import ASCENDING, DESCENDING, TEXT
from pymongo.errors import OperationFailure
from app.database.connection import DatabaseManager
from app.database.models import Company, Contact, ResearchSession, Task

logger = logging.getLogger(__name__)

class DatabaseInitializer:
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        
    def create_indexes(self):
        """Create indexes for all collections"""
        try:
            # Company indexes
            company_collection = self.db_manager.get_collection(Company.collection_name)
            company_collection.create_index([('name', TEXT), ('domain', TEXT)], name='company_search')
            company_collection.create_index([('domain', ASCENDING)], unique=True, name='unique_domain')
            company_collection.create_index([('company_number', ASCENDING)], sparse=True)
            
            # Contact indexes
            contact_collection = self.db_manager.get_collection(Contact.collection_name)
            contact_collection.create_index([('company_id', ASCENDING)], name='company_contacts')
            contact_collection.create_index([('email', ASCENDING)], sparse=True)
            contact_collection.create_index([('name', TEXT)], name='contact_search')
            
            # Research Session indexes
            session_collection = self.db_manager.get_collection(ResearchSession.collection_name)
            session_collection.create_index([('target_company_id', ASCENDING)], name='company_sessions')
            session_collection.create_index([('status', ASCENDING)])
            session_collection.create_index([('created_at', DESCENDING)])
            
            # Task indexes
            task_collection = self.db_manager.get_collection(Task.collection_name)
            task_collection.create_index([('session_id', ASCENDING)], name='session_tasks')
            task_collection.create_index([('status', ASCENDING)])
            task_collection.create_index([('created_at', DESCENDING)])
            
            logger.info("Successfully created all database indexes")
            return True
        except Exception as e:
            logger.error(f"Failed to create indexes: {str(e)}")
            return False
            
    def validate_collections(self) -> bool:
        """Validate that all required collections exist with correct schemas"""
        try:
            collections = self.db_manager.get_database().list_collection_names()
            required_collections = [
                Company.collection_name,
                Contact.collection_name,
                ResearchSession.collection_name,
                Task.collection_name
            ]
            
            for collection in required_collections:
                if collection not in collections:
                    logger.warning(f"Collection {collection} does not exist - will be created on first use")
                    
            return True
        except Exception as e:
            logger.error(f"Failed to validate collections: {str(e)}")
            return False
            
    def initialize_database(self) -> bool:
        """Initialize the database with required collections and indexes"""
        if not self.db_manager.connect():
            logger.error("Failed to connect to database")
            return False
            
        try:
            if not self.validate_collections():
                return False
                
            if not self.create_indexes():
                return False
                
            logger.info("Database initialization completed successfully")
            return True
        except Exception as e:
            logger.error(f"Database initialization failed: {str(e)}")
            return False
        finally:
            self.db_manager.disconnect()

def init_database(connection_string: str) -> bool:
    """Initialize the database with the given connection string"""
    db_manager = DatabaseManager(connection_string)
    initializer = DatabaseInitializer(db_manager)
    return initializer.initialize_database()

if __name__ == '__main__':
    import os
    connection_string = os.environ.get('MONGODB_URI', 'mongodb://localhost:27017/company_research')
    success = init_database(connection_string)
    exit(0 if success else 1) 
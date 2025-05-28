from typing import Dict, Any
import logging
from pymongo import ASCENDING, DESCENDING
from pymongo.errors import OperationFailure
from app.database.connection import DatabaseManager
from app.database.models.company import Company
from app.database.models.contact import Contact
from app.database.models.task import Task
from app.database.models.research_session import ResearchSession

logger = logging.getLogger(__name__)

def create_indexes(db_manager: DatabaseManager):
    """Create indexes for all collections"""
    try:
        # Company indexes
        companies = db_manager.get_collection(Company.collection_name)
        companies.create_index([('name', ASCENDING)], unique=True)
        companies.create_index([('domain', ASCENDING)], unique=True)
        companies.create_index([('industry', ASCENDING)])
        
        # Contact indexes
        contacts = db_manager.get_collection(Contact.collection_name)
        contacts.create_index([('company_id', ASCENDING)])
        contacts.create_index([('email', ASCENDING)])
        contacts.create_index([('name', ASCENDING)])
        
        # Task indexes
        tasks = db_manager.get_collection(Task.collection_name)
        tasks.create_index([('session_id', ASCENDING)])
        tasks.create_index([('status', ASCENDING)])
        tasks.create_index([('created_at', DESCENDING)])
        
        # Research Session indexes
        sessions = db_manager.get_collection(ResearchSession.collection_name)
        sessions.create_index([('target_company_id', ASCENDING)])
        sessions.create_index([('status', ASCENDING)])
        sessions.create_index([('created_at', DESCENDING)])
        
        logger.info("Successfully created all indexes")
        return True
        
    except OperationFailure as e:
        logger.error(f"Failed to create indexes: {str(e)}")
        return False

def setup_schema_validation(db_manager: DatabaseManager):
    """Setup schema validation for collections"""
    try:
        db = db_manager.get_database()
        
        # Company validation
        db.command({
            'collMod': Company.collection_name,
            'validator': {
                '$jsonSchema': {
                    'bsonType': 'object',
                    'required': ['name', 'domain'],
                    'properties': {
                        'name': {'bsonType': 'string'},
                        'domain': {'bsonType': 'string'},
                        'industry': {'bsonType': 'string'}
                    }
                }
            }
        })
        
        # Contact validation
        db.command({
            'collMod': Contact.collection_name,
            'validator': {
                '$jsonSchema': {
                    'bsonType': 'object',
                    'required': ['name', 'company_id'],
                    'properties': {
                        'name': {'bsonType': 'string'},
                        'company_id': {'bsonType': 'objectId'},
                        'email': {'bsonType': 'string'}
                    }
                }
            }
        })
        
        # Task validation
        db.command({
            'collMod': Task.collection_name,
            'validator': {
                '$jsonSchema': {
                    'bsonType': 'object',
                    'required': ['session_id', 'title', 'status'],
                    'properties': {
                        'session_id': {'bsonType': 'objectId'},
                        'title': {'bsonType': 'string'},
                        'status': {'bsonType': 'string'},
                        'progress': {'bsonType': 'double'}
                    }
                }
            }
        })
        
        # Research Session validation
        db.command({
            'collMod': ResearchSession.collection_name,
            'validator': {
                '$jsonSchema': {
                    'bsonType': 'object',
                    'required': ['target_company_id', 'research_type', 'status'],
                    'properties': {
                        'target_company_id': {'bsonType': 'objectId'},
                        'research_type': {'bsonType': 'string'},
                        'status': {'bsonType': 'string'},
                        'progress': {'bsonType': 'double'}
                    }
                }
            }
        })
        
        logger.info("Successfully setup schema validation")
        return True
        
    except OperationFailure as e:
        logger.error(f"Failed to setup schema validation: {str(e)}")
        return False

def init_database(connection_string: str) -> bool:
    """Initialize database with indexes and schema validation"""
    db_manager = DatabaseManager(connection_string)
    
    if not db_manager.connect():
        logger.error("Failed to connect to database")
        return False
        
    try:
        if not create_indexes(db_manager):
            return False
            
        if not setup_schema_validation(db_manager):
            return False
            
        logger.info("Database initialization completed successfully")
        return True
        
    except Exception as e:
        logger.error(f"Database initialization failed: {str(e)}")
        return False
    finally:
        db_manager.disconnect()

if __name__ == '__main__':
    import os
    from config import get_config
    
    config = get_config()
    mongo_url = os.environ.get('MONGODB_URL') or config.MONGODB_URL
    
    if init_database(mongo_url):
        print("Database initialized successfully")
    else:
        print("Database initialization failed") 
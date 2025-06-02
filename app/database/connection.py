from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
from typing import Optional
import logging

logger = logging.getLogger(__name__)

class DatabaseManager:
    _instance = None
    
    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, connection_string: str, database_name: str = "company_research"):
        # Only initialize if not already initialized
        if not hasattr(self, 'initialized'):
            self.connection_string = connection_string
            self.database_name = database_name
            self.client: Optional[MongoClient] = None
            self.db = None
            self.initialized = True
            
    def connect(self) -> bool:
        """Establish database connection with error handling"""
        try:
            if self.client is None:
                self.client = MongoClient(
                    self.connection_string,
                    serverSelectionTimeoutMS=5000,  # 5 second timeout
                    connectTimeoutMS=5000,
                    retryWrites=True,
                    w='majority',
                    retryReads=True,
                    maxPoolSize=50,
                    minPoolSize=10,
                    waitQueueTimeoutMS=5000,
                    appname='CompanyResearchTool'
                )
                # Test the connection with auth
                self.client.admin.command('ping')
                self.db = self.client[self.database_name]
                logger.info(f"Successfully connected to MongoDB: {self.database_name}")
                return True
            elif self.health_check():  # If client exists, verify it's healthy
                return True
            else:  # If client exists but unhealthy, reconnect
                self.disconnect()
                return self.connect()
        except (ConnectionFailure, ServerSelectionTimeoutError) as e:
            logger.error(f"Failed to connect to MongoDB: {str(e)}")
            self.client = None
            self.db = None
            return False
        except Exception as e:
            logger.error(f"Unexpected error connecting to MongoDB: {str(e)}")
            self.client = None
            self.db = None
            return False
            
    def disconnect(self):
        """Close database connection"""
        if self.client:
            self.client.close()
            self.client = None
            self.db = None
            logger.info("Disconnected from MongoDB")
            
    def health_check(self) -> bool:
        """Check if database is accessible"""
        try:
            if self.client:
                self.client.admin.command('ping')
                return True
            return False
        except Exception as e:
            logger.error(f"Database health check failed: {str(e)}")
            return False
    
    def get_database(self):
        """Get database instance, connecting if necessary"""
        if not self.client:
            self.connect()
        return self.db
    
    def get_collection(self, collection_name: str):
        """Get a specific collection"""
        if not self.client:
            self.connect()
        return self.db[collection_name] 
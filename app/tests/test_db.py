from app.database.connection import DatabaseManager
from app.database.models import Company, Contact, Task, TaskType, TaskStatus, ResearchSession, ResearchType, SessionStatus
import logging
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_database_operations():
    """Test basic database operations"""
    try:
        # Get MongoDB URL from environment or use default
        mongo_url = os.environ.get('MONGODB_URL', 'mongodb://localhost:27017/company_research_test')
        
        # Initialize database connection
        db_manager = DatabaseManager(mongo_url)
        
        # Test health check
        if not db_manager.connect():
            logger.error("Failed to connect to database")
            return False
            
        if not db_manager.health_check():
            logger.error("Health check failed")
            return False
            
        logger.info("Health check passed")
        
        # Create test company
        company = Company(
            name="Test Company",
            domain="testcompany.com",
            industry="Technology"
        )
        if not company.save(db_manager):
            logger.error("Failed to save company")
            return False
            
        logger.info(f"Created company with ID: {company._id}")
        
        # Create test research session
        session = ResearchSession(
            research_type=ResearchType.COMPANY_PROFILE,
            target_company_id=company._id,
            status=SessionStatus.IN_PROGRESS
        )
        if not session.save(db_manager):
            logger.error("Failed to save research session")
            return False
            
        logger.info(f"Created research session with ID: {session._id}")
        
        # Create test task
        task = Task(
            session_id=session._id,
            task_type=TaskType.RESEARCH,
            title="Test Task",
            status=TaskStatus.PENDING
        )
        if not task.save(db_manager):
            logger.error("Failed to save task")
            return False
            
        logger.info(f"Created task with ID: {task._id}")
        
        # List all tasks
        collection = db_manager.get_collection(Task.collection_name)
        tasks = list(collection.find({}))
        logger.info(f"Found {len(tasks)} tasks in database")
        for task in tasks:
            logger.info(f"Task: {task['title']} (ID: {task['_id']})")
        
        # Test cleanup
        task.delete(db_manager)
        session.delete(db_manager)
        company.delete(db_manager)
        
        logger.info("Test completed successfully")
        return True
        
    except Exception as e:
        logger.error(f"Test failed with error: {str(e)}")
        return False
    finally:
        db_manager.disconnect()

if __name__ == '__main__':
    success = test_database_operations()
    exit(0 if success else 1) 
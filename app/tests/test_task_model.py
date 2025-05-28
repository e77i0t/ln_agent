import pytest
from app.database.models import Task, ResearchSession, Company, TaskType, TaskStatus
from bson import ObjectId
from datetime import datetime

@pytest.fixture
def test_session(db_manager):
    company = Company(
        name="Task Test Company",
        domain="tasktest.com",
        industry="Technology"
    )
    company.save(db_manager)
    
    session = ResearchSession(
        research_type="COMPANY_PROFILE",
        target_company_id=company._id,
        status="IN_PROGRESS"
    )
    session.save(db_manager)
    
    yield session
    
    session.delete(db_manager)
    company.delete(db_manager)

def test_task_creation_validation(test_session):
    """Test task model validation during creation."""
    # Test required fields
    with pytest.raises(ValueError):
        Task()  # Should fail without required fields
    
    with pytest.raises(ValueError):
        Task(title="Test")  # Missing session_id and task_type
        
    # Test valid creation
    task = Task(
        session_id=test_session._id,
        task_type=TaskType.RESEARCH,
        title="Test Task",
        status=TaskStatus.PENDING
    )
    assert task.title == "Test Task"
    assert task.session_id == test_session._id
    assert task.status == TaskStatus.PENDING

def test_task_crud_operations(db_manager, test_session):
    """Test CRUD operations for Task model."""
    # Create
    task = Task(
        session_id=test_session._id,
        task_type=TaskType.RESEARCH,
        title="CRUD Test Task",
        description="Test task for CRUD operations",
        status=TaskStatus.PENDING,
        priority=1
    )
    assert task.save(db_manager) is True
    assert task._id is not None
    
    # Read
    collection = db_manager.get_collection(Task.collection_name)
    found = collection.find_one({"_id": task._id})
    assert found is not None
    assert found["title"] == "CRUD Test Task"
    
    # Update
    task.status = TaskStatus.IN_PROGRESS
    task.priority = 2
    assert task.save(db_manager) is True
    updated = collection.find_one({"_id": task._id})
    assert updated["status"] == TaskStatus.IN_PROGRESS
    assert updated["priority"] == 2
    
    # Delete
    assert task.delete(db_manager) is True
    deleted = collection.find_one({"_id": task._id})
    assert deleted is None

def test_task_serialization(test_session):
    """Test task serialization methods."""
    task_data = {
        "session_id": test_session._id,
        "task_type": TaskType.RESEARCH,
        "title": "Serialization Test",
        "description": "Test task",
        "status": TaskStatus.PENDING,
        "priority": 1,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }
    
    # Test from_dict
    task = Task.from_dict(task_data)
    assert task.title == task_data["title"]
    assert task.status == task_data["status"]
    
    # Test to_dict
    serialized = task.to_dict()
    assert serialized["title"] == task_data["title"]
    assert serialized["status"] == task_data["status"]
    assert "created_at" in serialized
    assert "updated_at" in serialized

def test_task_error_handling(db_manager, test_session):
    """Test error handling in Task model operations."""
    # Test invalid task type
    with pytest.raises(ValueError):
        Task(
            session_id=test_session._id,
            task_type="INVALID_TYPE",  # Invalid task type
            title="Test Task",
            status=TaskStatus.PENDING
        )
    
    # Test invalid status
    with pytest.raises(ValueError):
        Task(
            session_id=test_session._id,
            task_type=TaskType.RESEARCH,
            title="Test Task",
            status="INVALID_STATUS"  # Invalid status
        )
    
    # Test invalid priority
    with pytest.raises(ValueError):
        Task(
            session_id=test_session._id,
            task_type=TaskType.RESEARCH,
            title="Test Task",
            status=TaskStatus.PENDING,
            priority=-1  # Invalid priority
        )
    
    # Test non-existent session_id
    task = Task(
        session_id=ObjectId(),  # Non-existent session_id
        task_type=TaskType.RESEARCH,
        title="Test Task",
        status=TaskStatus.PENDING
    )
    assert task.save(db_manager) is False  # Should fail due to foreign key constraint 
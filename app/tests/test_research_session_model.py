import pytest
from app.database.models import ResearchSession, Company, ResearchType, SessionStatus
from bson import ObjectId
from datetime import datetime

@pytest.fixture
def test_company(db_manager):
    company = Company(
        name="Session Test Company",
        domain="sessiontest.com",
        industry="Technology"
    )
    company.save(db_manager)
    yield company
    company.delete(db_manager)

def test_session_creation_validation(test_company):
    """Test research session model validation during creation."""
    # Test required fields
    with pytest.raises(ValueError):
        ResearchSession()  # Should fail without required fields
    
    with pytest.raises(ValueError):
        ResearchSession(research_type=ResearchType.COMPANY_PROFILE)  # Missing target_company_id
        
    # Test valid creation
    session = ResearchSession(
        research_type=ResearchType.COMPANY_PROFILE,
        target_company_id=test_company._id,
        status=SessionStatus.IN_PROGRESS
    )
    assert session.research_type == ResearchType.COMPANY_PROFILE
    assert session.target_company_id == test_company._id
    assert session.status == SessionStatus.IN_PROGRESS

def test_session_crud_operations(db_manager, test_company):
    """Test CRUD operations for ResearchSession model."""
    # Create
    session = ResearchSession(
        research_type=ResearchType.COMPANY_PROFILE,
        target_company_id=test_company._id,
        status=SessionStatus.IN_PROGRESS,
        notes="Test session for CRUD operations",
        priority=1
    )
    assert session.save(db_manager) is True
    assert session._id is not None
    
    # Read
    collection = db_manager.get_collection(ResearchSession.collection_name)
    found = collection.find_one({"_id": session._id})
    assert found is not None
    assert found["research_type"] == ResearchType.COMPANY_PROFILE
    
    # Update
    session.status = SessionStatus.COMPLETED
    session.priority = 2
    assert session.save(db_manager) is True
    updated = collection.find_one({"_id": session._id})
    assert updated["status"] == SessionStatus.COMPLETED
    assert updated["priority"] == 2
    
    # Delete
    assert session.delete(db_manager) is True
    deleted = collection.find_one({"_id": session._id})
    assert deleted is None

def test_session_serialization(test_company):
    """Test research session serialization methods."""
    session_data = {
        "research_type": ResearchType.COMPANY_PROFILE,
        "target_company_id": test_company._id,
        "status": SessionStatus.IN_PROGRESS,
        "notes": "Test session",
        "priority": 1,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }
    
    # Test from_dict
    session = ResearchSession.from_dict(session_data)
    assert session.research_type == session_data["research_type"]
    assert session.status == session_data["status"]
    
    # Test to_dict
    serialized = session.to_dict()
    assert serialized["research_type"] == session_data["research_type"]
    assert serialized["status"] == session_data["status"]
    assert "created_at" in serialized
    assert "updated_at" in serialized

def test_session_error_handling(db_manager, test_company):
    """Test error handling in ResearchSession model operations."""
    # Test invalid research type
    with pytest.raises(ValueError):
        ResearchSession(
            research_type="INVALID_TYPE",  # Invalid research type
            target_company_id=test_company._id,
            status=SessionStatus.IN_PROGRESS
        )
    
    # Test invalid status
    with pytest.raises(ValueError):
        ResearchSession(
            research_type=ResearchType.COMPANY_PROFILE,
            target_company_id=test_company._id,
            status="INVALID_STATUS"  # Invalid status
        )
    
    # Test invalid priority
    with pytest.raises(ValueError):
        ResearchSession(
            research_type=ResearchType.COMPANY_PROFILE,
            target_company_id=test_company._id,
            status=SessionStatus.IN_PROGRESS,
            priority=-1  # Invalid priority
        )
    
    # Test non-existent target_company_id
    session = ResearchSession(
        research_type=ResearchType.COMPANY_PROFILE,
        target_company_id=ObjectId(),  # Non-existent company_id
        status=SessionStatus.IN_PROGRESS
    )
    assert session.save(db_manager) is False  # Should fail due to foreign key constraint 
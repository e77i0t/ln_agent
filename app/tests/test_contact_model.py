import pytest
from app.database.models import Contact, Company
from bson import ObjectId
from datetime import datetime

@pytest.fixture
def test_company(db_manager):
    company = Company(
        name="Contact Test Company",
        domain="contacttest.com",
        industry="Technology"
    )
    company.save(db_manager)
    yield company
    company.delete(db_manager)

def test_contact_creation_validation(test_company):
    """Test contact model validation during creation."""
    # Test required fields
    with pytest.raises(ValueError):
        Contact()  # Should fail without required fields
    
    with pytest.raises(ValueError):
        Contact(name="Test")  # Missing company_id
        
    # Test valid creation
    contact = Contact(
        name="Test Contact",
        company_id=test_company._id,
        title="Test Title",
        email="test@example.com",
        source="linkedin"
    )
    assert contact.name == "Test Contact"
    assert contact.company_id == test_company._id
    assert contact.source == "linkedin"

def test_contact_crud_operations(db_manager, test_company):
    """Test CRUD operations for Contact model."""
    # Create
    contact = Contact(
        name="CRUD Test Contact",
        company_id=test_company._id,
        title="Test Manager",
        email="crud@test.com",
        phone="+1234567890",
        linkedin_profile="https://linkedin.com/in/crudtest",
        notes="Test contact for CRUD operations",
        source="linkedin"
    )
    assert contact.save(db_manager) is True
    assert contact._id is not None
    
    # Read
    collection = db_manager.get_collection(Contact.collection_name)
    found = collection.find_one({"_id": contact._id})
    assert found is not None
    assert found["name"] == "CRUD Test Contact"
    assert found["source"] == "linkedin"
    
    # Update
    contact.title = "Senior Test Manager"
    contact.source = "website"
    assert contact.save(db_manager) is True
    updated = collection.find_one({"_id": contact._id})
    assert updated["title"] == "Senior Test Manager"
    assert updated["source"] == "website"
    
    # Delete
    assert contact.delete(db_manager) is True
    deleted = collection.find_one({"_id": contact._id})
    assert deleted is None

def test_contact_serialization(test_company):
    """Test contact serialization methods."""
    contact_data = {
        "name": "Serialization Test",
        "company_id": test_company._id,
        "title": "Test Title",
        "email": "ser@test.com",
        "phone": "+1234567890",
        "linkedin_profile": "https://linkedin.com/in/sertest",
        "notes": "Test notes",
        "source": "manual",
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }
    
    # Test from_dict
    contact = Contact.from_dict(contact_data)
    assert contact.name == contact_data["name"]
    assert contact.email == contact_data["email"]
    assert contact.source == contact_data["source"]
    
    # Test to_dict
    serialized = contact.to_dict()
    assert serialized["name"] == contact_data["name"]
    assert serialized["email"] == contact_data["email"]
    assert serialized["source"] == contact_data["source"]
    assert "created_at" in serialized
    assert "updated_at" in serialized

def test_contact_error_handling(db_manager, test_company):
    """Test error handling in Contact model operations."""
    # Test duplicate email
    contact1 = Contact(
        name="Error Test 1",
        company_id=test_company._id,
        email="error@test.com",
        title="Test Title",
        source="linkedin"
    )
    contact1.save(db_manager)
    
    contact2 = Contact(
        name="Error Test 2",
        company_id=test_company._id,
        email="error@test.com",  # Same email
        title="Test Title",
        source="website"  # Different source
    )
    # Should fail due to duplicate email
    assert contact2.save(db_manager) is False
    
    # Test invalid data types
    with pytest.raises(ValueError):
        Contact(
            name=123,  # Invalid type for name
            company_id=test_company._id,
            email="test@example.com",
            title="Test"
        )
    
    # Test invalid email format
    with pytest.raises(ValueError):
        Contact(
            name="Test",
            company_id=test_company._id,
            email="invalid-email",  # Invalid email format
            title="Test"
        )
    
    # Clean up
    contact1.delete(db_manager) 
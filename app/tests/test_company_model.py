import pytest
from app.database.models import Company
from bson import ObjectId
from datetime import datetime

def test_company_creation_validation():
    """Test company model validation during creation."""
    # Test required fields
    with pytest.raises(ValueError):
        Company()  # Should fail without required fields
    
    with pytest.raises(ValueError):
        Company(name="Test")  # Missing domain
        
    # Test valid creation
    company = Company(
        name="Test Company",
        domain="test.com",
        industry="Technology"
    )
    assert company.name == "Test Company"
    assert company.domain == "test.com"

def test_company_crud_operations(db_manager):
    """Test CRUD operations for Company model."""
    # Create
    company = Company(
        name="CRUD Test Company",
        domain="crudtest.com",
        industry="Technology",
        size="1-10",
        headquarters="Test Location",
        description="Test company for CRUD operations",
        linkedin_url="https://linkedin.com/company/crudtest",
        website_data={"test": True}
    )
    assert company.save(db_manager) is True
    assert company._id is not None
    
    # Read
    collection = db_manager.get_collection(Company.collection_name)
    found = collection.find_one({"_id": company._id})
    assert found is not None
    assert found["name"] == "CRUD Test Company"
    
    # Update
    company.size = "11-50"
    assert company.save(db_manager) is True
    updated = collection.find_one({"_id": company._id})
    assert updated["size"] == "11-50"
    
    # Delete
    assert company.delete(db_manager) is True
    deleted = collection.find_one({"_id": company._id})
    assert deleted is None

def test_company_serialization():
    """Test company serialization methods."""
    company_data = {
        "name": "Serialization Test",
        "domain": "sertest.com",
        "industry": "Technology",
        "size": "1-10",
        "headquarters": "Test HQ",
        "description": "Test company",
        "linkedin_url": "https://linkedin.com/company/sertest",
        "website_data": {"test": True},
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }
    
    # Test from_dict
    company = Company.from_dict(company_data)
    assert company.name == company_data["name"]
    assert company.domain == company_data["domain"]
    
    # Test to_dict
    serialized = company.to_dict()
    assert serialized["name"] == company_data["name"]
    assert serialized["domain"] == company_data["domain"]
    assert "created_at" in serialized
    assert "updated_at" in serialized

def test_company_error_handling(db_manager):
    """Test error handling in Company model operations."""
    # Test duplicate domain
    company1 = Company(
        name="Error Test 1",
        domain="errortest.com",
        industry="Technology"
    )
    company1.save(db_manager)
    
    company2 = Company(
        name="Error Test 2",
        domain="errortest.com",  # Same domain
        industry="Technology"
    )
    # Should fail due to duplicate domain
    assert company2.save(db_manager) is False
    
    # Test invalid data types
    with pytest.raises(ValueError):
        Company(
            name=123,  # Invalid type for name
            domain="test.com",
            industry="Technology"
        )
    
    # Clean up
    company1.delete(db_manager) 
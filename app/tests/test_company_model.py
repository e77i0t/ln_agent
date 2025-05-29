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
        industry="Technology",
        company_number="12345",
        jurisdiction="US"
    )
    assert company.name == "Test Company"
    assert company.domain == "test.com"
    assert company.company_number == "12345"
    assert company.jurisdiction == "US"

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
        website_data={"test": True},
        opencorporates_data={"registration_number": "12345", "jurisdiction_code": "us_de"},
        company_number="12345",
        jurisdiction="US-DE"
    )
    assert company.save(db_manager) is True
    assert company._id is not None
    
    # Read
    collection = db_manager.get_collection(Company.collection_name)
    found = collection.find_one({"_id": company._id})
    assert found is not None
    assert found["name"] == "CRUD Test Company"
    assert found["company_number"] == "12345"
    assert found["jurisdiction"] == "US-DE"
    
    # Update
    company.size = "11-50"
    company.opencorporates_data["status"] = "active"
    assert company.save(db_manager) is True
    updated = collection.find_one({"_id": company._id})
    assert updated["size"] == "11-50"
    assert updated["opencorporates_data"]["status"] == "active"
    
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
        "opencorporates_data": {
            "registration_number": "12345",
            "jurisdiction_code": "us_de",
            "status": "active"
        },
        "company_number": "12345",
        "jurisdiction": "US-DE",
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }
    
    # Test from_dict
    company = Company.from_dict(company_data)
    assert company.name == company_data["name"]
    assert company.domain == company_data["domain"]
    assert company.company_number == company_data["company_number"]
    assert company.jurisdiction == company_data["jurisdiction"]
    assert company.opencorporates_data == company_data["opencorporates_data"]
    
    # Test to_dict
    serialized = company.to_dict()
    assert serialized["name"] == company_data["name"]
    assert serialized["domain"] == company_data["domain"]
    assert serialized["company_number"] == company_data["company_number"]
    assert serialized["jurisdiction"] == company_data["jurisdiction"]
    assert serialized["opencorporates_data"] == company_data["opencorporates_data"]
    assert "created_at" in serialized
    assert "updated_at" in serialized

def test_company_error_handling(db_manager):
    """Test error handling in Company model operations."""
    # Test duplicate domain
    company1 = Company(
        name="Error Test 1",
        domain="errortest.com",
        industry="Technology",
        company_number="12345",
        jurisdiction="US"
    )
    company1.save(db_manager)
    
    company2 = Company(
        name="Error Test 2",
        domain="errortest.com",  # Same domain
        industry="Technology",
        company_number="67890",  # Different company number
        jurisdiction="UK"  # Different jurisdiction
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
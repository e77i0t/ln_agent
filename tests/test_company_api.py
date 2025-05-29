import pytest
from bson import ObjectId
from datetime import datetime

def test_create_test_company(client):
    """Test creating a test company via the API endpoint."""
    response = client.post('/test/company')
    assert response.status_code == 201
    
    data = response.json
    assert data['status'] == 'success'
    assert data['message'] == 'Test company created successfully'
    assert 'company' in data
    
    company = data['company']
    assert 'id' in company
    assert ObjectId.is_valid(company['id'])
    assert company['name'].startswith('Test Company ')
    assert company['domain'].startswith('testcompany')
    assert company['company_number'].startswith('TEST')
    assert company['jurisdiction'] == 'US-DE'

def test_create_test_company_db_error(client, monkeypatch):
    """Test creating a test company when database connection fails."""
    from app.database.connection import DatabaseManager
    
    def mock_connect(self):
        return False
    
    monkeypatch.setattr(DatabaseManager, 'connect', mock_connect)
    
    response = client.post('/test/company')
    assert response.status_code == 500
    
    data = response.json
    assert data['status'] == 'error'
    assert data['message'] == 'Failed to connect to database'

def test_create_test_company_save_error(client, monkeypatch):
    """Test creating a test company when saving fails."""
    from app.database.models import Company
    
    def mock_save(self, db_manager):
        return False
    
    monkeypatch.setattr(Company, 'save', mock_save)
    
    response = client.post('/test/company')
    assert response.status_code == 500
    
    data = response.json
    assert data['status'] == 'error'
    assert data['message'] == 'Failed to save company' 
"""
Tests for the research API endpoints.
Tests are designed to run in sequence, with dependencies between tests.
"""

import pytest
from flask import url_for
import time
from datetime import datetime
import json

@pytest.fixture(scope='module')
def test_client():
    """Create a test client for the app"""
    from app import create_app
    app = create_app('testing')
    
    # Create a test client
    with app.test_client() as testing_client:
        with app.app_context():
            yield testing_client

@pytest.fixture(scope='module')
def test_session_data():
    """Test data for creating a research session"""
    return {
        'company_name': 'Test Company Inc',
        'research_type': 'general',
        'target_person': 'John Doe',
        'additional_context': 'Testing the research API'
    }

class TestResearchAPI:
    session_id = None  # Will store session ID for dependent tests
    
    def test_health_check(self, test_client):
        """Test the API health check endpoint"""
        response = test_client.get('/api/health')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['status'] == 'healthy'
        assert data['message'] == 'API is running'

    def test_start_research_missing_fields(self, test_client):
        """Test starting research with missing required fields"""
        response = test_client.post('/api/research/start',
                                  json={},
                                  content_type='application/json')
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data
        assert 'missing_fields' in data
        assert set(data['missing_fields']) == {'company_name', 'research_type'}

    def test_start_research_invalid_type(self, test_client, test_session_data):
        """Test starting research with invalid research type"""
        invalid_data = test_session_data.copy()
        invalid_data['research_type'] = 'invalid_type'
        
        response = test_client.post('/api/research/start',
                                  json=invalid_data,
                                  content_type='application/json')
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data
        assert 'Invalid research type' in data['error']

    def test_start_research_success(self, test_client, test_session_data):
        """Test successfully starting a research session"""
        response = test_client.post('/api/research/start',
                                  json=test_session_data,
                                  content_type='application/json')
        assert response.status_code == 201
        data = json.loads(response.data)
        assert 'session_id' in data
        assert 'status' in data
        assert data['message'] == 'Research session started successfully'
        
        # Store session_id for dependent tests
        TestResearchAPI.session_id = data['session_id']

    def test_get_status_invalid_session(self, test_client):
        """Test getting status for invalid session ID"""
        response = test_client.get('/api/research/invalid_id/status')
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data

    def test_get_status_success(self, test_client):
        """Test getting status for valid session ID"""
        assert TestResearchAPI.session_id is not None, "No session ID from previous test"
        
        response = test_client.get(f'/api/research/{TestResearchAPI.session_id}/status')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['session_id'] == TestResearchAPI.session_id
        assert 'status' in data
        assert 'tasks' in data
        assert 'progress' in data
        assert isinstance(data['progress'], int)
        assert 0 <= data['progress'] <= 100

    def test_get_results_invalid_session(self, test_client):
        """Test getting results for invalid session ID"""
        response = test_client.get('/api/research/invalid_id/results')
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data

    def test_get_results_success(self, test_client):
        """Test getting results for valid session ID"""
        assert TestResearchAPI.session_id is not None, "No session ID from previous test"
        
        response = test_client.get(f'/api/research/{TestResearchAPI.session_id}/results')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['session_id'] == TestResearchAPI.session_id
        assert 'status' in data
        assert 'research_type' in data
        assert 'company' in data

    def test_company_search(self, test_client, test_session_data):
        """Test company search endpoint"""
        company_name = test_session_data['company_name']
        response = test_client.get(f'/api/companies/search?q={company_name}')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'companies' in data
        assert 'count' in data
        assert isinstance(data['companies'], list)
        assert isinstance(data['count'], int)

    def test_get_company_details(self, test_client):
        """Test getting company details"""
        # First search for the company to get its ID
        response = test_client.get('/api/companies/search?q=Test Company')
        data = json.loads(response.data)
        
        if data['count'] > 0:
            company_id = data['companies'][0]['_id']
            
            # Now get the company details
            response = test_client.get(f'/api/companies/{company_id}')
            assert response.status_code == 200
            data = json.loads(response.data)
            assert '_id' in data
            assert 'name' in data
            assert 'domain' in data

    def test_get_company_not_found(self, test_client):
        """Test getting non-existent company"""
        response = test_client.get('/api/companies/000000000000000000000000')
        assert response.status_code == 404
        data = json.loads(response.data)
        assert 'error' in data
        assert data['error'] == 'Company not found' 
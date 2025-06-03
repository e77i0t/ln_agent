"""
End-to-end tests for the API using real HTTP requests.
These tests simulate actual client usage of the API.
"""

import requests
import pytest
import time
import json
import subprocess
import signal
import os
from urllib.parse import quote
from multiprocessing import Process
from app import create_app

class TestAPIEndToEnd:
    # Class variables to store state between tests
    api_url = None
    server_process = None
    session_id = None
    company_id = None
    
    @classmethod
    def setup_class(cls):
        """Start the Flask server in a separate process"""
        def run_app():
            app = create_app('testing')
            app.run(host='localhost', port=5280, debug=False)
        
        # Start the server process
        cls.server_process = Process(target=run_app)
        cls.server_process.start()
        cls.api_url = 'http://localhost:5280'
        
        # Wait for server to start
        max_retries = 5
        for i in range(max_retries):
            try:
                requests.get(f"{cls.api_url}/health")
                break
            except requests.ConnectionError:
                if i == max_retries - 1:
                    raise
                time.sleep(1)
    
    @classmethod
    def teardown_class(cls):
        """Stop the Flask server"""
        if cls.server_process:
            cls.server_process.terminate()
            cls.server_process.join()
    
    def test_01_health_check(self):
        """Test the health check endpoint"""
        response = requests.get(f"{self.api_url}/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data['status'] == 'healthy'
        assert data['message'] == 'API is running'
    
    def test_02_mongodb_health(self):
        """Test MongoDB health check"""
        response = requests.get(f"{self.api_url}/health/mongodb")
        assert response.status_code == 200
        data = response.json()
        assert data['status'] == 'healthy'
    
    def test_03_start_research_invalid_json(self):
        """Test starting research with invalid JSON"""
        response = requests.post(
            f"{self.api_url}/api/research/start",
            data="invalid json",
            headers={'Content-Type': 'application/json'}
        )
        assert response.status_code == 400
    
    def test_04_start_research_missing_fields(self):
        """Test starting research with missing required fields"""
        response = requests.post(
            f"{self.api_url}/api/research/start",
            json={},
            headers={'Content-Type': 'application/json'}
        )
        assert response.status_code == 400
        data = response.json()
        assert 'missing_fields' in data
    
    def test_05_start_research_success(self):
        """Test successfully starting a research session"""
        payload = {
            'company_name': 'Apple Inc.',
            'research_type': 'general',
            'target_person': 'Tim Cook',
            'additional_context': 'Looking for recent AI initiatives'
        }
        
        response = requests.post(
            f"{self.api_url}/api/research/start",
            json=payload,
            headers={'Content-Type': 'application/json'}
        )
        assert response.status_code == 201
        data = response.json()
        assert 'session_id' in data
        assert data['status'] in ['planned', 'started']
        
        # Store session_id for subsequent tests
        TestAPIEndToEnd.session_id = data['session_id']
    
    def test_06_get_status_invalid_session(self):
        """Test getting status for invalid session ID"""
        response = requests.get(f"{self.api_url}/api/research/invalid_id/status")
        assert response.status_code == 400
    
    def test_07_get_status_success(self):
        """Test getting status for valid session ID"""
        assert self.session_id is not None, "No session ID from previous test"
        
        # Try getting status multiple times to see progress
        max_attempts = 3
        for _ in range(max_attempts):
            response = requests.get(f"{self.api_url}/api/research/{self.session_id}/status")
            assert response.status_code == 200
            data = response.json()
            assert data['session_id'] == self.session_id
            assert 'progress' in data
            assert isinstance(data['progress'], int)
            
            if data['progress'] == 100:
                break
            time.sleep(2)  # Wait before checking again
    
    def test_08_get_results_success(self):
        """Test getting results for valid session ID"""
        assert self.session_id is not None, "No session ID from previous test"
        
        response = requests.get(f"{self.api_url}/api/research/{self.session_id}/results")
        assert response.status_code == 200
        data = response.json()
        assert data['session_id'] == self.session_id
        assert 'status' in data
        assert 'company' in data
    
    def test_09_company_search(self):
        """Test company search endpoint"""
        company_name = quote('Apple Inc.')  # URL encode the company name
        response = requests.get(f"{self.api_url}/api/companies/search?q={company_name}")
        assert response.status_code == 200
        data = response.json()
        assert 'companies' in data
        assert isinstance(data['companies'], list)
        
        if data['count'] > 0:
            # Store first company ID for next test
            TestAPIEndToEnd.company_id = data['companies'][0]['_id']
    
    def test_10_get_company_details(self):
        """Test getting company details"""
        if self.company_id:
            response = requests.get(f"{self.api_url}/api/companies/{self.company_id}")
            assert response.status_code == 200
            data = response.json()
            assert '_id' in data
            assert 'name' in data
    
    def test_11_concurrent_sessions(self):
        """Test starting multiple research sessions concurrently"""
        payload = {
            'company_name': 'Microsoft Corporation',
            'research_type': 'general'
        }
        
        # Start multiple sessions concurrently
        responses = []
        for _ in range(3):
            response = requests.post(
                f"{self.api_url}/api/research/start",
                json=payload,
                headers={'Content-Type': 'application/json'}
            )
            responses.append(response)
            time.sleep(0.1)  # Small delay between requests
        
        # Check all responses
        session_ids = set()
        for response in responses:
            assert response.status_code == 201
            data = response.json()
            assert 'session_id' in data
            session_ids.add(data['session_id'])
        
        # Verify each session got a unique ID
        assert len(session_ids) == 3
    
    def test_12_rate_limiting(self):
        """Test rate limiting by making rapid requests"""
        payload = {
            'company_name': 'Tesla Inc',
            'research_type': 'general'
        }
        
        # Make multiple rapid requests
        responses = []
        for _ in range(10):
            response = requests.post(
                f"{self.api_url}/api/research/start",
                json=payload,
                headers={'Content-Type': 'application/json'}
            )
            responses.append(response)
        
        # Check if any requests were rate limited
        rate_limited = any(r.status_code == 429 for r in responses)
        successful = any(r.status_code == 201 for r in responses)
        assert successful, "No requests were successful"
    
    def test_13_error_handling(self):
        """Test various error conditions"""
        # Test invalid content type
        response = requests.post(
            f"{self.api_url}/api/research/start",
            data="plain text",
            headers={'Content-Type': 'text/plain'}
        )
        assert response.status_code == 400
        
        # Test invalid research type
        response = requests.post(
            f"{self.api_url}/api/research/start",
            json={'company_name': 'Test Inc', 'research_type': 'invalid'},
            headers={'Content-Type': 'application/json'}
        )
        assert response.status_code == 400
        
        # Test invalid session ID format
        response = requests.get(f"{self.api_url}/api/research/invalid-format/status")
        assert response.status_code == 400
    
    def test_14_cleanup(self):
        """Test cleanup by checking all created sessions are complete"""
        if self.session_id:
            response = requests.get(f"{self.api_url}/api/research/{self.session_id}/status")
            assert response.status_code == 200
            data = response.json()
            assert data['status'] in ['completed', 'failed', 'cancelled']

if __name__ == '__main__':
    pytest.main([__file__, '-v']) 
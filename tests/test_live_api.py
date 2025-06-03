#!/usr/bin/env python3
"""
Live API testing script.
Tests a running instance of the API using direct HTTP requests.
Similar to using curl commands but automated.

Usage:
    python test_live_api.py [--host http://localhost:5280]
"""

import requests
import json
import time
import argparse
from urllib.parse import quote
from datetime import datetime
from typing import Dict, Any, Optional

class APITester:
    def __init__(self, base_url: str = "http://localhost:5280"):
        self.base_url = base_url.rstrip('/')
        self.session_id = None
        self.company_id = None
        self.test_results = []
        
    def log_test(self, name: str, passed: bool, response: requests.Response, error: Optional[str] = None):
        """Log test results with details"""
        result = {
            'test': name,
            'passed': passed,
            'timestamp': datetime.now().isoformat(),
            'status_code': response.status_code if response else None,
            'error': error,
            'response': response.json() if response and response.headers.get('content-type', '').startswith('application/json') else None
        }
        self.test_results.append(result)
        
        # Print immediate feedback
        status = "✅" if passed else "❌"
        print(f"{status} {name}")
        if error:
            print(f"   Error: {error}")
        if not passed and response:
            print(f"   Response: {response.text[:200]}...")
        print()

    def test_health_endpoints(self):
        """Test all health check endpoints"""
        try:
            # Test main health endpoint
            response = requests.get(f"{self.base_url}/health")
            self.log_test(
                "Main Health Check",
                response.status_code == 200 and response.json()['status'] == 'healthy',
                response
            )

            # Test MongoDB health
            response = requests.get(f"{self.base_url}/health/mongodb")
            self.log_test(
                "MongoDB Health Check",
                response.status_code == 200 and response.json()['status'] == 'healthy',
                response
            )

            # Test Redis health
            response = requests.get(f"{self.base_url}/health/redis")
            self.log_test(
                "Redis Health Check",
                response.status_code == 200 and response.json()['status'] == 'healthy',
                response
            )

            # Test all services health
            response = requests.get(f"{self.base_url}/health/all")
            self.log_test(
                "All Services Health Check",
                response.status_code == 200 and response.json()['status'] == 'healthy',
                response
            )
        except requests.RequestException as e:
            self.log_test("Health Checks", False, None, str(e))

    def test_research_workflow(self):
        """Test the complete research workflow"""
        try:
            # Start research session
            payload = {
                'company_name': 'Apple Inc.',
                'research_type': 'general',
                'target_person': 'Tim Cook',
                'additional_context': 'Testing the live API'
            }
            
            response = requests.post(
                f"{self.base_url}/api/research/start",
                json=payload,
                headers={'Content-Type': 'application/json'}
            )
            
            success = response.status_code == 201 and 'session_id' in response.json()
            self.log_test("Start Research Session", success, response)
            
            if success:
                self.session_id = response.json()['session_id']
                
                # Check status multiple times
                max_checks = 3
                for i in range(max_checks):
                    response = requests.get(
                        f"{self.base_url}/api/research/{self.session_id}/status"
                    )
                    success = response.status_code == 200
                    self.log_test(f"Check Research Status (Attempt {i+1})", success, response)
                    
                    if success and response.json().get('progress') == 100:
                        break
                    time.sleep(2)
                
                # Get final results
                response = requests.get(
                    f"{self.base_url}/api/research/{self.session_id}/results"
                )
                self.log_test("Get Research Results", response.status_code == 200, response)
                
        except requests.RequestException as e:
            self.log_test("Research Workflow", False, None, str(e))

    def test_company_endpoints(self):
        """Test company-related endpoints"""
        try:
            # Search for company
            company_name = quote('Apple Inc.')
            response = requests.get(
                f"{self.base_url}/api/companies/search?q={company_name}"
            )
            success = response.status_code == 200
            self.log_test("Company Search", success, response)
            
            if success and response.json().get('count', 0) > 0:
                self.company_id = response.json()['companies'][0]['_id']
                
                # Get company details
                response = requests.get(
                    f"{self.base_url}/api/companies/{self.company_id}"
                )
                self.log_test("Get Company Details", response.status_code == 200, response)
                
        except requests.RequestException as e:
            self.log_test("Company Endpoints", False, None, str(e))

    def test_error_handling(self):
        """Test various error conditions"""
        try:
            # Test invalid JSON
            response = requests.post(
                f"{self.base_url}/api/research/start",
                data="invalid json",
                headers={'Content-Type': 'application/json'}
            )
            self.log_test(
                "Invalid JSON Handling",
                response.status_code == 400,
                response
            )

            # Test missing required fields
            response = requests.post(
                f"{self.base_url}/api/research/start",
                json={},
                headers={'Content-Type': 'application/json'}
            )
            self.log_test(
                "Missing Fields Handling",
                response.status_code == 400 and 'missing_fields' in response.json(),
                response
            )

            try:
                # Test invalid session ID
                response = requests.get(
                    f"{self.base_url}/api/research/invalid_id/status"
                )
                success = response.status_code == 404 and 'error' in response.json()
                self.log_test(
                    "Invalid Session ID Handling",
                    success,
                    response,
                    None if success else f"Expected 404 with error message, got {response.status_code}"
                )
            except requests.RequestException as e:
                self.log_test(
                    "Invalid Session ID Handling",
                    False,
                    None,
                    f"Request failed: {str(e)}"
                )

        except requests.RequestException as e:
            self.log_test("Error Handling", False, None, str(e))

    def run_all_tests(self):
        """Run all test cases"""
        print(f"\nTesting API at {self.base_url}\n")
        
        self.test_health_endpoints()
        self.test_research_workflow()
        self.test_company_endpoints()
        self.test_error_handling()
        
        # Print summary
        total = len(self.test_results)
        passed = sum(1 for r in self.test_results if r['passed'])
        failed = total - passed
        
        print("\nTest Summary:")
        print(f"Total Tests: {total}")
        print(f"Passed: {passed}")
        print(f"Failed: {failed}")
        
        # Save results to file
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"api_test_results_{timestamp}.json"
        with open(filename, 'w') as f:
            json.dump(self.test_results, f, indent=2)
        print(f"\nDetailed results saved to: {filename}")

def main():
    parser = argparse.ArgumentParser(description='Test live API endpoints')
    parser.add_argument('--host', default='http://localhost:5280',
                       help='API host URL (default: http://localhost:5280)')
    args = parser.parse_args()
    
    tester = APITester(args.host)
    tester.run_all_tests()

if __name__ == '__main__':
    main() 
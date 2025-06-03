"""
OpenCorporates API integration for retrieving official company data.
"""
from typing import List, Dict, Any, Optional
import requests
from urllib.parse import urljoin
import logging
from .base_scraper import BaseScraper

class OpenCorporatesScraper(BaseScraper):
    """Scraper for the OpenCorporates API."""
    
    def __init__(self, api_key: Optional[str] = None, delay_range=(1, 3)):
        """
        Initialize the OpenCorporates scraper.
        
        Args:
            api_key (str, optional): OpenCorporates API key
            delay_range (tuple): Min and max delay between requests in seconds
        """
        super().__init__(delay_range=delay_range)
        self.api_key = api_key
        self.base_url = "https://api.opencorporates.com/v0.4/"
        self.logger = logging.getLogger(__name__)
        
        # Update headers for API requests
        self.session.headers.update({
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        })
    
    def _make_request(self, endpoint: str, params: Dict = None) -> Optional[Dict]:
        """
        Make an API request with error handling.
        
        Args:
            endpoint (str): API endpoint to call
            params (Dict, optional): Query parameters
            
        Returns:
            Optional[Dict]: JSON response data or None if request fails
        """
        url = urljoin(self.base_url, endpoint)
        params = params or {}
        
        # Add API key if available
        if self.api_key:
            params['api_token'] = self.api_key
        
        try:
            self.respect_delay()
            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            self.logger.error(f"Error making request to {endpoint}: {str(e)}")
            return None
    
    def search_companies(self, company_name: str, jurisdiction: str = None) -> List[Dict]:
        """
        Search for companies by name.
        
        Args:
            company_name (str): Name of the company to search for
            jurisdiction (str, optional): Jurisdiction code (e.g., 'gb', 'us_de')
            
        Returns:
            List[Dict]: List of matching companies
        """
        params = {'q': company_name}
        if jurisdiction:
            params['jurisdiction_code'] = jurisdiction
        
        response = self._make_request('companies/search', params)
        if not response or 'results' not in response:
            return []
        
        return response['results'].get('companies', [])
    
    def get_company_details(self, company_number: str, jurisdiction: str) -> Dict[str, Any]:
        """
        Get detailed company information.
        
        Args:
            company_number (str): Company registration number
            jurisdiction (str): Jurisdiction code
            
        Returns:
            Dict[str, Any]: Company details
        """
        endpoint = f'companies/{jurisdiction}/{company_number}'
        response = self._make_request(endpoint)
        
        if not response or 'results' not in response:
            return {}
        
        return response['results'].get('company', {})
    
    def get_company_officers(self, company_number: str, jurisdiction: str) -> List[Dict]:
        """
        Get company officers and directors.
        
        Args:
            company_number (str): Company registration number
            jurisdiction (str): Jurisdiction code
            
        Returns:
            List[Dict]: List of company officers
        """
        endpoint = f'companies/{jurisdiction}/{company_number}/officers'
        response = self._make_request(endpoint)
        
        if not response or 'results' not in response:
            return []
        
        return response['results'].get('officers', [])
    
    def get_company_filings(self, company_number: str, jurisdiction: str) -> List[Dict]:
        """
        Get recent company filings.
        
        Args:
            company_number (str): Company registration number
            jurisdiction (str): Jurisdiction code
            
        Returns:
            List[Dict]: List of company filings
        """
        endpoint = f'companies/{jurisdiction}/{company_number}/filings'
        response = self._make_request(endpoint)
        
        if not response or 'results' not in response:
            return []
        
        return response['results'].get('filings', [])
    
    def get_company_network(self, company_number: str, jurisdiction: str) -> Dict[str, Any]:
        """
        Get company network information (relationships).
        
        Args:
            company_number (str): Company registration number
            jurisdiction (str): Jurisdiction code
            
        Returns:
            Dict[str, Any]: Company network data
        """
        endpoint = f'companies/{jurisdiction}/{company_number}/network'
        response = self._make_request(endpoint)
        
        if not response or 'results' not in response:
            return {}
        
        return response['results'].get('network', {})
    
    def search_officers(self, name: str, jurisdiction: str = None) -> List[Dict]:
        """
        Search for company officers by name.
        
        Args:
            name (str): Officer name to search for
            jurisdiction (str, optional): Jurisdiction code
            
        Returns:
            List[Dict]: List of matching officers
        """
        params = {'q': name}
        if jurisdiction:
            params['jurisdiction_code'] = jurisdiction
        
        response = self._make_request('officers/search', params)
        if not response or 'results' not in response:
            return []
        
        return response['results'].get('officers', []) 
"""
Example script demonstrating the use of the company research scraping infrastructure.
"""
import logging
import json
from typing import Dict, Any

from app.scrapers.company_website_scraper import CompanyWebsiteScraper
from app.scrapers.opencorporates_scraper import OpenCorporatesScraper

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def research_company(domain: str, company_name: str = None, jurisdiction: str = None) -> Dict[str, Any]:
    """
    Research a company using both website scraping and OpenCorporates data.
    
    Args:
        domain (str): Company website domain
        company_name (str, optional): Company name for OpenCorporates search
        jurisdiction (str, optional): Company jurisdiction for OpenCorporates
        
    Returns:
        Dict[str, Any]: Combined company information
    """
    company_data = {
        'website_data': None,
        'opencorporates_data': None
    }
    
    # Scrape company website
    logger.info(f"Scraping website data for {domain}")
    website_scraper = CompanyWebsiteScraper()
    company_data['website_data'] = website_scraper.scrape_company_info(domain)
    
    # Get OpenCorporates data if name is provided
    if company_name:
        logger.info(f"Fetching OpenCorporates data for {company_name}")
        oc_scraper = OpenCorporatesScraper()  # Add your API key here if you have one
        
        # Search for the company
        companies = oc_scraper.search_companies(company_name, jurisdiction)
        if companies:
            company = companies[0]  # Use the first match
            company_number = company.get('company_number')
            company_jurisdiction = company.get('jurisdiction_code')
            
            if company_number and company_jurisdiction:
                # Get detailed information
                details = oc_scraper.get_company_details(company_number, company_jurisdiction)
                officers = oc_scraper.get_company_officers(company_number, company_jurisdiction)
                filings = oc_scraper.get_company_filings(company_number, company_jurisdiction)
                
                company_data['opencorporates_data'] = {
                    'details': details,
                    'officers': officers,
                    'filings': filings
                }
    
    return company_data

def main():
    """Main function to demonstrate the scraping infrastructure."""
    # Example usage
    companies_to_research = [
        {
            'domain': 'example.com',
            'name': 'Example Company Inc',
            'jurisdiction': 'us_de'  # Delaware, USA
        }
    ]
    
    for company in companies_to_research:
        logger.info(f"Researching company: {company['name']}")
        try:
            data = research_company(
                domain=company['domain'],
                company_name=company['name'],
                jurisdiction=company.get('jurisdiction')
            )
            
            # Save results to a JSON file
            output_file = f"company_data_{company['domain'].replace('.', '_')}.json"
            with open(output_file, 'w') as f:
                json.dump(data, f, indent=2)
            logger.info(f"Saved research results to {output_file}")
            
        except Exception as e:
            logger.error(f"Error researching {company['name']}: {str(e)}")

if __name__ == '__main__':
    main() 
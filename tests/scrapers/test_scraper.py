"""
Test script for the web scraping infrastructure.
"""
import logging
from pprint import pprint

from app.scrapers.company_website_scraper import CompanyWebsiteScraper
from app.scrapers.opencorporates_scraper import OpenCorporatesScraper

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_website_scraper():
    """Test the website scraper with a real company website."""
    # Initialize the scraper with conservative rate limiting
    scraper = CompanyWebsiteScraper(delay_range=(3, 5))
    
    # Test with Mozilla's website (they have good robots.txt policies)
    domain = "mozilla.org"
    logger.info(f"Testing website scraper with {domain}")
    
    try:
        # Scrape company information
        company_info = scraper.scrape_company_info(domain)
        
        # Print the results
        logger.info("Scraped data:")
        pprint(company_info)
        
        # Basic validation
        assert company_info['domain'] == domain, "Domain mismatch"
        assert isinstance(company_info['social_links'], dict), "Social links should be a dictionary"
        
        if company_info['about_text']:
            logger.info("Successfully found about text")
        
        if company_info['contact_info']:
            logger.info("Successfully found contact information")
            
        if company_info['team_members']:
            logger.info(f"Found {len(company_info['team_members'])} team members")
            
        if company_info['job_listings']:
            logger.info(f"Found {len(company_info['job_listings'])} job listings")
            
        logger.info("Website scraper test completed successfully")
        
    except Exception as e:
        logger.error(f"Error during website scraping: {str(e)}")
        raise

def test_opencorporates_scraper():
    """Test the OpenCorporates scraper."""
    # Initialize the scraper
    scraper = OpenCorporatesScraper()  # Add your API key if you have one
    
    # Test with a well-known company
    company_name = "Mozilla Corporation"
    jurisdiction = "us_de"  # Delaware
    
    logger.info(f"Testing OpenCorporates scraper with {company_name}")
    
    try:
        # Search for the company
        companies = scraper.search_companies(company_name, jurisdiction)
        
        if companies:
            logger.info(f"Found {len(companies)} matching companies")
            
            # Get details for the first match
            company = companies[0]
            company_number = company.get('company_number')
            company_jurisdiction = company.get('jurisdiction_code')
            
            if company_number and company_jurisdiction:
                # Get detailed information
                details = scraper.get_company_details(company_number, company_jurisdiction)
                logger.info("Company details:")
                pprint(details)
                
                # Get officers
                officers = scraper.get_company_officers(company_number, company_jurisdiction)
                if officers:
                    logger.info(f"Found {len(officers)} company officers")
                
                # Get filings
                filings = scraper.get_company_filings(company_number, company_jurisdiction)
                if filings:
                    logger.info(f"Found {len(filings)} company filings")
        
        logger.info("OpenCorporates scraper test completed successfully")
        
    except Exception as e:
        logger.error(f"Error during OpenCorporates scraping: {str(e)}")
        raise

if __name__ == "__main__":
    logger.info("Starting scraper tests")
    
    # Test website scraper
    test_website_scraper()
    
    # Test OpenCorporates scraper
    test_opencorporates_scraper() 
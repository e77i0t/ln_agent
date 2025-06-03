"""
Scraper for extracting company information from their websites.
"""
from typing import Dict, List, Any, Optional
from urllib.parse import urljoin, urlparse
import logging
import re

from bs4 import BeautifulSoup

from .base_scraper import BaseScraper
from .utils.html_parser import HTMLParser

class CompanyWebsiteScraper(BaseScraper):
    """Scraper for extracting structured information from company websites."""
    
    # Common patterns for finding relevant pages
    CAREERS_PATTERNS = [
        r'/careers?/?$',
        r'/jobs/?$',
        r'/work-(?:with|for)-us/?$',
        r'/join-us/?$',
        r'/opportunities/?$'
    ]
    
    ABOUT_PATTERNS = [
        r'/about/?$',
        r'/about-us/?$',
        r'/who-we-are/?$',
        r'/company/?$'
    ]
    
    TEAM_PATTERNS = [
        r'/team/?$',
        r'/people/?$',
        r'/leadership/?$',
        r'/management/?$'
    ]
    
    CONTACT_PATTERNS = [
        r'/contact/?$',
        r'/contact-us/?$',
        r'/get-in-touch/?$'
    ]
    
    def __init__(self, delay_range=(2, 4), max_retries=3):
        """
        Initialize the company website scraper.
        
        Args:
            delay_range (tuple): Min and max delay between requests in seconds
            max_retries (int): Maximum number of retry attempts for failed requests
        """
        super().__init__(delay_range=delay_range, max_retries=max_retries)
        self.logger = logging.getLogger(__name__)
        self.html_parser = HTMLParser()
    
    def scrape_company_info(self, domain: str) -> Dict[str, Any]:
        """
        Extract comprehensive company information from their website.
        
        Args:
            domain (str): Company website domain
            
        Returns:
            Dict[str, Any]: Structured company information
        """
        base_url = f"https://{domain}"
        company_info = {
            'domain': domain,
            'about_text': None,
            'contact_info': {},
            'team_members': [],
            'careers_page': None,
            'job_listings': [],
            'company_size_hints': [],
            'locations': [],
            'social_links': {},
            'metadata': {}
        }
        
        # Scrape homepage
        homepage_soup = self.scrape_url(base_url)
        if not homepage_soup:
            self.logger.error(f"Failed to scrape homepage for {domain}")
            return company_info
        
        # Extract metadata and social links from homepage
        company_info['metadata'] = HTMLParser.extract_metadata(homepage_soup)
        company_info['social_links'] = HTMLParser.find_social_links(homepage_soup)
        
        # Find and scrape about page
        about_url = self._find_page_url(homepage_soup, base_url, self.ABOUT_PATTERNS)
        if about_url:
            about_soup = self.scrape_url(about_url)
            if about_soup:
                company_info['about_text'] = HTMLParser.extract_main_content(about_soup)
        
        # Find and scrape contact page
        contact_url = self._find_page_url(homepage_soup, base_url, self.CONTACT_PATTERNS)
        if contact_url:
            contact_soup = self.scrape_url(contact_url)
            if contact_soup:
                company_info['contact_info'] = self.extract_contact_info(contact_soup)
        
        # Find and scrape team page
        team_url = self._find_page_url(homepage_soup, base_url, self.TEAM_PATTERNS)
        if team_url:
            team_soup = self.scrape_url(team_url)
            if team_soup:
                company_info['team_members'] = self.extract_team_members(team_soup)
        
        # Find and scrape careers page
        careers_url = self._find_page_url(homepage_soup, base_url, self.CAREERS_PATTERNS)
        if careers_url:
            company_info['careers_page'] = careers_url
            careers_soup = self.scrape_url(careers_url)
            if careers_soup:
                company_info['job_listings'] = self.extract_job_listings(careers_soup)
        
        # Extract locations from contact and about pages
        company_info['locations'] = self.extract_locations(homepage_soup)
        if about_soup:
            company_info['locations'].extend(self.extract_locations(about_soup))
        if contact_soup:
            company_info['locations'].extend(self.extract_locations(contact_soup))
        company_info['locations'] = list(set(company_info['locations']))
        
        # Look for company size hints
        company_info['company_size_hints'] = self.find_company_size_hints(
            [homepage_soup, about_soup, careers_soup] if about_soup and careers_soup else [homepage_soup]
        )
        
        return company_info
    
    def _find_page_url(self, soup: BeautifulSoup, base_url: str, patterns: List[str]) -> Optional[str]:
        """Find URL for a specific type of page based on patterns."""
        for link in soup.find_all('a', href=True):
            href = link['href']
            absolute_url = urljoin(base_url, href)
            
            # Skip external links
            if not absolute_url.startswith(base_url):
                continue
            
            # Check against patterns
            path = urlparse(absolute_url).path
            for pattern in patterns:
                if re.search(pattern, path, re.IGNORECASE):
                    return absolute_url
        
        return None
    
    def extract_contact_info(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Extract contact information from page."""
        contact_info = {
            'emails': [],
            'phones': [],
            'addresses': [],
            'social_links': {}
        }
        
        # Get all text content
        text_content = soup.get_text()
        
        # Extract emails and phones
        contact_info['emails'] = HTMLParser.extract_emails(text_content)
        contact_info['phones'] = HTMLParser.extract_phone_numbers(text_content)
        
        # Extract social links
        contact_info['social_links'] = HTMLParser.find_social_links(soup)
        
        # Try to find physical addresses
        address_elements = soup.find_all(['address', 'div'], class_=lambda x: x and 'address' in x.lower())
        for element in address_elements:
            addr = HTMLParser.clean_text(element.get_text())
            if addr:
                contact_info['addresses'].append(addr)
        
        return contact_info
    
    def extract_team_members(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """Extract team member information."""
        team_members = []
        
        # Look for common team member containers
        member_elements = soup.find_all(['div', 'article'], class_=lambda x: x and any(
            term in x.lower() for term in ['team-member', 'person', 'profile', 'bio']
        ))
        
        for element in member_elements:
            member = {
                'name': None,
                'title': None,
                'bio': None,
                'image_url': None,
                'social_links': {}
            }
            
            # Try to find name (usually in a heading)
            name_elem = element.find(['h2', 'h3', 'h4', 'h5'])
            if name_elem:
                member['name'] = HTMLParser.clean_text(name_elem.get_text())
            
            # Try to find title
            title_elem = element.find(['p', 'div'], class_=lambda x: x and 'title' in str(x).lower())
            if title_elem:
                member['title'] = HTMLParser.clean_text(title_elem.get_text())
            
            # Try to find bio
            bio_elem = element.find(['p', 'div'], class_=lambda x: x and 'bio' in str(x).lower())
            if bio_elem:
                member['bio'] = HTMLParser.clean_text(bio_elem.get_text())
            
            # Try to find image
            img_elem = element.find('img')
            if img_elem and img_elem.get('src'):
                member['image_url'] = img_elem['src']
            
            # Find social links
            member['social_links'] = HTMLParser.find_social_links(element)
            
            if member['name']:  # Only add if we found a name
                team_members.append(member)
        
        return team_members
    
    def extract_job_listings(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """Extract job listings from careers page."""
        jobs = []
        
        # Look for job posting containers
        job_elements = soup.find_all(['div', 'article'], class_=lambda x: x and any(
            term in str(x).lower() for term in ['job-posting', 'position', 'vacancy', 'opening']
        ))
        
        for element in job_elements:
            job = {
                'title': None,
                'department': None,
                'location': None,
                'description': None,
                'url': None
            }
            
            # Try to find title
            title_elem = element.find(['h2', 'h3', 'h4', 'a'])
            if title_elem:
                job['title'] = HTMLParser.clean_text(title_elem.get_text())
                # Check for job URL in title link
                if title_elem.name == 'a' and title_elem.get('href'):
                    job['url'] = title_elem['href']
            
            # Try to find department
            dept_elem = element.find(['div', 'span'], class_=lambda x: x and 'department' in str(x).lower())
            if dept_elem:
                job['department'] = HTMLParser.clean_text(dept_elem.get_text())
            
            # Try to find location
            loc_elem = element.find(['div', 'span'], class_=lambda x: x and 'location' in str(x).lower())
            if loc_elem:
                job['location'] = HTMLParser.clean_text(loc_elem.get_text())
            
            # Try to find description
            desc_elem = element.find(['div', 'p'], class_=lambda x: x and 'description' in str(x).lower())
            if desc_elem:
                job['description'] = HTMLParser.clean_text(desc_elem.get_text())
            
            if job['title']:  # Only add if we found a title
                jobs.append(job)
        
        return jobs
    
    def extract_locations(self, soup: BeautifulSoup) -> List[str]:
        """Extract location information from page."""
        locations = set()
        
        # Look for location containers
        location_elements = soup.find_all(['div', 'p'], class_=lambda x: x and 'location' in str(x).lower())
        for element in location_elements:
            loc = HTMLParser.clean_text(element.get_text())
            if loc:
                locations.add(loc)
        
        # Look for address elements
        address_elements = soup.find_all('address')
        for element in address_elements:
            addr = HTMLParser.clean_text(element.get_text())
            if addr:
                locations.add(addr)
        
        return list(locations)
    
    def find_company_size_hints(self, soups: List[BeautifulSoup]) -> List[str]:
        """Find hints about company size from various pages."""
        size_hints = set()
        
        # Regular expressions for finding employee count references
        size_patterns = [
            r'(\d+)\+?\s*employees',
            r'team of (\d+)\+?',
            r'over (\d+) people',
            r'(\d+)\+? people worldwide',
            r'grown to (\d+)\+?'
        ]
        
        for soup in soups:
            if not soup:
                continue
                
            text_content = soup.get_text()
            
            # Look for matches in text content
            for pattern in size_patterns:
                matches = re.finditer(pattern, text_content, re.IGNORECASE)
                for match in matches:
                    size_hints.add(match.group(0))
        
        return list(size_hints) 
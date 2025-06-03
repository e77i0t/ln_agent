"""
Base scraper class providing core functionality for web scraping.
"""
import logging
import random
import time
from typing import List, Optional, Dict
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

from app.scrapers.utils.rate_limiter import RateLimiter
from app.scrapers.utils.robots_checker import RobotsChecker

class BaseScraper:
    """Base class for all scrapers with common functionality."""
    
    def __init__(self, delay_range=(1, 3), max_retries=3):
        """
        Initialize the base scraper.
        
        Args:
            delay_range (tuple): Min and max delay between requests in seconds
            max_retries (int): Maximum number of retry attempts for failed requests
        """
        self.delay_range = delay_range
        self.max_retries = max_retries
        self.session = requests.Session()
        self.logger = logging.getLogger(self.__class__.__name__)
        self.rate_limiter = RateLimiter()
        self.robots_checker = RobotsChecker()
        
        # Set reasonable default headers
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
        })
    
    def scrape_url(self, url: str, parse_robots=True) -> Optional[BeautifulSoup]:
        """
        Scrape a URL with error handling and rate limiting.
        
        Args:
            url (str): The URL to scrape
            parse_robots (bool): Whether to check robots.txt before scraping
            
        Returns:
            Optional[BeautifulSoup]: Parsed HTML content or None if scraping fails
        """
        domain = urlparse(url).netloc
        
        # Check robots.txt if enabled
        if parse_robots and not self.robots_checker.can_fetch(url, self.session.headers['User-Agent']):
            self.logger.warning(f"URL {url} is not allowed by robots.txt")
            return None
            
        # Check rate limiting
        if not self.rate_limiter.can_make_request(domain):
            self.logger.warning(f"Rate limit exceeded for domain {domain}")
            return None
            
        for attempt in range(self.max_retries):
            try:
                # Respect delay between requests
                self.respect_delay()
                
                # Make the request
                response = self.session.get(url, timeout=30)
                response.raise_for_status()
                
                # Record the request
                self.rate_limiter.record_request(domain)
                
                # Parse and return the content
                return BeautifulSoup(response.text, 'html.parser')
                
            except requests.RequestException as e:
                self.logger.error(f"Error scraping {url} (attempt {attempt + 1}/{self.max_retries}): {str(e)}")
                if attempt == self.max_retries - 1:
                    return None
                time.sleep(2 ** attempt)  # Exponential backoff
    
    def respect_delay(self):
        """Wait between requests using the configured delay range."""
        delay = random.uniform(*self.delay_range)
        time.sleep(delay)
    
    def extract_links(self, soup: BeautifulSoup, base_url: str) -> List[str]:
        """
        Extract and normalize links from page.
        
        Args:
            soup (BeautifulSoup): Parsed HTML content
            base_url (str): Base URL for resolving relative links
            
        Returns:
            List[str]: List of normalized URLs
        """
        links = []
        for anchor in soup.find_all('a', href=True):
            href = anchor['href']
            absolute_url = urljoin(base_url, href)
            # Filter out non-HTTP(S) URLs and fragments
            if absolute_url.startswith(('http://', 'https://')):
                links.append(absolute_url)
        return list(set(links))  # Remove duplicates
    
    def get_domain(self, url: str) -> str:
        """Extract domain from URL."""
        return urlparse(url).netloc
    
    def update_headers(self, headers: Dict[str, str]):
        """Update session headers with new values."""
        self.session.headers.update(headers) 
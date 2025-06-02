"""
Robots.txt parser and checker utility.
"""
import time
from typing import Dict, Optional
from urllib.parse import urlparse
from urllib.robotparser import RobotFileParser
import logging
import requests

class RobotsChecker:
    """Utility class to check robots.txt rules and manage crawl delays."""
    
    def __init__(self, cache_ttl: int = 3600):
        """
        Initialize the robots checker.
        
        Args:
            cache_ttl (int): Time in seconds to cache robots.txt content
        """
        self.robot_parsers: Dict[str, RobotFileParser] = {}
        self.cache_ttl = cache_ttl
        self.last_fetch: Dict[str, float] = {}
        self.logger = logging.getLogger(__name__)
    
    def _get_robots_url(self, url: str) -> str:
        """
        Get the robots.txt URL for a given URL.
        
        Args:
            url (str): The URL to check
            
        Returns:
            str: The URL of the robots.txt file
        """
        parsed = urlparse(url)
        return f"{parsed.scheme}://{parsed.netloc}/robots.txt"
    
    def _fetch_robots_txt(self, domain: str) -> Optional[RobotFileParser]:
        """
        Fetch and parse robots.txt for a domain.
        
        Args:
            domain (str): The domain to fetch robots.txt for
            
        Returns:
            Optional[RobotFileParser]: Parser for the robots.txt file, or None if unavailable
        """
        robots_url = self._get_robots_url(f"https://{domain}")
        
        try:
            response = requests.get(robots_url, timeout=10)
            if response.status_code == 200:
                parser = RobotFileParser()
                parser.parse(response.text.splitlines())
                return parser
        except requests.RequestException as e:
            self.logger.warning(f"Failed to fetch robots.txt for {domain}: {str(e)}")
        
        return None
    
    def _get_parser(self, url: str) -> Optional[RobotFileParser]:
        """
        Get a cached or new robots.txt parser for a URL.
        
        Args:
            url (str): The URL to get a parser for
            
        Returns:
            Optional[RobotFileParser]: The parser instance or None if unavailable
        """
        domain = urlparse(url).netloc
        current_time = time.time()
        
        # Check if we need to refresh the cache
        if (domain not in self.robot_parsers or
            domain not in self.last_fetch or
            current_time - self.last_fetch[domain] > self.cache_ttl):
            
            parser = self._fetch_robots_txt(domain)
            if parser:
                self.robot_parsers[domain] = parser
                self.last_fetch[domain] = current_time
        
        return self.robot_parsers.get(domain)
    
    def can_fetch(self, url: str, user_agent: str = '*') -> bool:
        """
        Check if we can fetch this URL according to robots.txt.
        
        Args:
            url (str): The URL to check
            user_agent (str): The user agent to check for
            
        Returns:
            bool: True if allowed to fetch, False otherwise
        """
        parser = self._get_parser(url)
        if not parser:
            # If we can't fetch robots.txt, assume it's allowed
            return True
        
        return parser.can_fetch(user_agent, url)
    
    def get_crawl_delay(self, url: str, user_agent: str = '*') -> Optional[float]:
        """
        Get recommended crawl delay from robots.txt.
        
        Args:
            url (str): The URL to check
            user_agent (str): The user agent to check for
            
        Returns:
            Optional[float]: The crawl delay in seconds, or None if not specified
        """
        parser = self._get_parser(url)
        if not parser:
            return None
            
        try:
            return parser.crawl_delay(user_agent)
        except AttributeError:
            return None
    
    def clear_cache(self, domain: str = None):
        """
        Clear the robots.txt cache.
        
        Args:
            domain (str, optional): Specific domain to clear, or all if None
        """
        if domain:
            self.robot_parsers.pop(domain, None)
            self.last_fetch.pop(domain, None)
        else:
            self.robot_parsers.clear()
            self.last_fetch.clear() 
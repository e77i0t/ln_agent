"""
HTML parsing utilities for extracting structured data from web pages.
"""
import re
from typing import List, Dict, Optional
from bs4 import BeautifulSoup
import unicodedata

class HTMLParser:
    """Utility class for parsing and extracting data from HTML content."""
    
    # Common patterns for data extraction
    EMAIL_PATTERN = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
    PHONE_PATTERN = r'(?:\+\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}'
    SOCIAL_DOMAINS = {
        'linkedin.com': 'linkedin',
        'twitter.com': 'twitter',
        'facebook.com': 'facebook',
        'instagram.com': 'instagram',
        'github.com': 'github'
    }
    
    @staticmethod
    def extract_emails(text: str) -> List[str]:
        """
        Extract email addresses from text.
        
        Args:
            text (str): Text to extract emails from
            
        Returns:
            List[str]: List of unique email addresses
        """
        emails = re.findall(HTMLParser.EMAIL_PATTERN, text)
        return list(set(emails))
    
    @staticmethod
    def extract_phone_numbers(text: str) -> List[str]:
        """
        Extract phone numbers from text.
        
        Args:
            text (str): Text to extract phone numbers from
            
        Returns:
            List[str]: List of unique phone numbers
        """
        phones = re.findall(HTMLParser.PHONE_PATTERN, text)
        # Clean up and standardize format
        cleaned = [re.sub(r'[^\d+]', '', phone) for phone in phones]
        return list(set(cleaned))
    
    @staticmethod
    def clean_text(text: str) -> str:
        """
        Clean and normalize text content.
        
        Args:
            text (str): Text to clean
            
        Returns:
            str: Cleaned text
        """
        if not text:
            return ""
            
        # Convert to unicode and normalize
        text = unicodedata.normalize('NFKC', text)
        
        # Replace multiple whitespace with single space
        text = re.sub(r'\s+', ' ', text)
        
        # Remove leading/trailing whitespace
        text = text.strip()
        
        return text
    
    @staticmethod
    def find_social_links(soup: BeautifulSoup) -> Dict[str, str]:
        """
        Find social media links in HTML content.
        
        Args:
            soup (BeautifulSoup): Parsed HTML content
            
        Returns:
            Dict[str, str]: Dictionary mapping social media platforms to their URLs
        """
        social_links = {}
        
        for link in soup.find_all('a', href=True):
            href = link['href'].lower()
            
            # Check against known social media domains
            for domain, platform in HTMLParser.SOCIAL_DOMAINS.items():
                if domain in href:
                    social_links[platform] = href
                    break
        
        return social_links
    
    @staticmethod
    def extract_structured_data(soup: BeautifulSoup) -> Dict[str, str]:
        """
        Extract structured data (Schema.org, OpenGraph, etc.) from HTML.
        
        Args:
            soup (BeautifulSoup): Parsed HTML content
            
        Returns:
            Dict[str, str]: Dictionary of structured data properties
        """
        data = {}
        
        # Extract OpenGraph metadata
        for meta in soup.find_all('meta', property=re.compile(r'^og:')):
            property_name = meta.get('property', '').replace('og:', '')
            content = meta.get('content', '')
            if property_name and content:
                data[f'og_{property_name}'] = content
        
        # Extract Schema.org JSON-LD data
        for script in soup.find_all('script', type='application/ld+json'):
            try:
                import json
                json_data = json.loads(script.string)
                if isinstance(json_data, dict):
                    data.update(json_data)
            except (json.JSONDecodeError, AttributeError):
                continue
        
        return data
    
    @staticmethod
    def extract_main_content(soup: BeautifulSoup) -> Optional[str]:
        """
        Extract the main content from a webpage, attempting to filter out navigation, ads, etc.
        
        Args:
            soup (BeautifulSoup): Parsed HTML content
            
        Returns:
            Optional[str]: The main content text, if found
        """
        # Try to find main content area
        main_tags = ['main', 'article', 'div[role="main"]', '.main-content', '#main-content']
        
        for tag in main_tags:
            main_content = soup.select_one(tag)
            if main_content:
                # Remove unwanted elements
                for unwanted in main_content.find_all(['script', 'style', 'nav', 'header', 'footer']):
                    unwanted.decompose()
                
                return HTMLParser.clean_text(main_content.get_text())
        
        return None
    
    @staticmethod
    def extract_metadata(soup: BeautifulSoup) -> Dict[str, str]:
        """
        Extract metadata from HTML head section.
        
        Args:
            soup (BeautifulSoup): Parsed HTML content
            
        Returns:
            Dict[str, str]: Dictionary of metadata
        """
        metadata = {}
        
        # Title
        title_tag = soup.find('title')
        if title_tag:
            metadata['title'] = HTMLParser.clean_text(title_tag.string)
        
        # Meta description
        description = soup.find('meta', attrs={'name': 'description'})
        if description:
            metadata['description'] = description.get('content', '')
        
        # Meta keywords
        keywords = soup.find('meta', attrs={'name': 'keywords'})
        if keywords:
            metadata['keywords'] = keywords.get('content', '')
        
        return metadata 
# Company Research Tool - Web Scraping Infrastructure

A robust and respectful web scraping system for gathering company information from websites and the OpenCorporates API.

## Features

- HTTP-based scraping with requests and BeautifulSoup
- OpenCorporates API integration
- Rate limiting and respectful scraping practices
- User-agent rotation and header management
- Error handling and retry logic
- Robots.txt compliance checking
- Structured data extraction

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd company-research-tool
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

### Basic Example

```python
from app.scrapers.company_website_scraper import CompanyWebsiteScraper
from app.scrapers.opencorporates_scraper import OpenCorporatesScraper

# Initialize scrapers
website_scraper = CompanyWebsiteScraper()
oc_scraper = OpenCorporatesScraper(api_key='your_api_key')  # API key optional

# Scrape company website
company_info = website_scraper.scrape_company_info('example.com')

# Search OpenCorporates
companies = oc_scraper.search_companies('Example Company Inc', jurisdiction='us_de')
```

### Example Script

See `examples/company_research.py` for a complete example of how to use the scraping infrastructure.

## Components

### Base Scraper
- Rate limiting
- Error handling
- Retry logic
- Header management

### Company Website Scraper
- Extracts company information from websites
- Finds and scrapes relevant pages (About, Contact, Team, Careers)
- Structured data extraction

### OpenCorporates Scraper
- Company search
- Detailed company information
- Officer and director information
- Company filings

### Utilities
- HTML parsing
- Rate limiting
- Robots.txt checking

## Configuration

### Rate Limiting
Configure rate limiting in the scraper initialization:
```python
scraper = CompanyWebsiteScraper(delay_range=(2, 4))  # 2-4 seconds between requests
```

### OpenCorporates API
Set your API key when initializing the OpenCorporates scraper:
```python
scraper = OpenCorporatesScraper(api_key='your_api_key')
```

## Best Practices

1. Always respect robots.txt
2. Use reasonable delays between requests
3. Handle errors gracefully
4. Log all scraping activity
5. Use appropriate user agents
6. Check terms of service for target websites

## Data Structure

### Company Website Data
```python
{
    'domain': str,
    'about_text': str,
    'contact_info': {
        'emails': List[str],
        'phones': List[str],
        'addresses': List[str],
        'social_links': Dict[str, str]
    },
    'team_members': List[Dict],
    'careers_page': str,
    'job_listings': List[Dict],
    'company_size_hints': List[str],
    'locations': List[str],
    'social_links': Dict[str, str],
    'metadata': Dict[str, str]
}
```

### OpenCorporates Data
```python
{
    'details': Dict,
    'officers': List[Dict],
    'filings': List[Dict]
}
```

## Error Handling

The infrastructure includes comprehensive error handling:
- Network errors
- Rate limiting
- Invalid responses
- Missing data
- API errors

## Logging

Logging is configured to track:
- Scraping activity
- Errors and warnings
- Rate limiting
- API calls

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- OpenCorporates API
- Beautiful Soup
- Requests library
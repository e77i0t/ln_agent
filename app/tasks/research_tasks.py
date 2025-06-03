from celery import current_task
from app.tasks.celery_app import celery
from app.services.task_service import TaskService
from app.scrapers.company_website_scraper import CompanyWebsiteScraper
from app.scrapers.opencorporates_scraper import OpenCorporatesScraper
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)
task_service = TaskService()

@celery.task(bind=True, max_retries=3)
def scrape_company_website(self, task_id: str, company_name: str, domain: str) -> Dict[str, Any]:
    """Celery task to scrape company website"""
    try:
        # Update task status
        task_service.update_task_status(
            task_id, 
            'in_progress',
            progress=10,
            current_step='Initializing website scraper'
        )
        
        # Initialize scraper
        scraper = CompanyWebsiteScraper()
        
        # Update progress
        self.update_state(state='PROGRESS', meta={'current': 25, 'total': 100})
        task_service.update_task_status(
            task_id,
            'in_progress',
            progress=25,
            current_step='Scraping company website'
        )
        
        # Perform scraping
        company_data = scraper.scrape_company_info(domain)
        
        # Update progress
        self.update_state(state='PROGRESS', meta={'current': 75, 'total': 100})
        task_service.update_task_status(
            task_id,
            'in_progress',
            progress=75,
            current_step='Processing scraped data'
        )
        
        # Complete task
        task_service.complete_task(task_id, result_data=company_data)
        
        return {
            'status': 'completed',
            'data': company_data
        }
        
    except Exception as e:
        logger.error(f"Task {task_id} failed: {str(e)}")
        task_service.fail_task(task_id, error_message=str(e))
        
        # Retry with exponential backoff
        retry_count = self.request.retries
        if retry_count < self.max_retries:
            self.retry(countdown=2 ** retry_count * 60)  # 1min, 2min, 4min
            
        raise

@celery.task(bind=True, max_retries=3)
def lookup_opencorporates_data(self, task_id: str, company_name: str) -> Dict[str, Any]:
    """Celery task to get OpenCorporates data"""
    try:
        task_service.update_task_status(
            task_id,
            'in_progress',
            progress=10,
            current_step='Initializing OpenCorporates lookup'
        )
        
        scraper = OpenCorporatesScraper()
        
        # Search for company
        self.update_state(state='PROGRESS', meta={'current': 30, 'total': 100})
        task_service.update_task_status(
            task_id,
            'in_progress',
            progress=30,
            current_step='Searching for company'
        )
        
        companies = scraper.search_companies(company_name)
        
        if companies:
            # Get detailed data for first match
            self.update_state(state='PROGRESS', meta={'current': 60, 'total': 100})
            task_service.update_task_status(
                task_id,
                'in_progress',
                progress=60,
                current_step='Fetching company details'
            )
            
            company = companies[0]
            details = scraper.get_company_details(
                company['company_number'],
                company['jurisdiction']
            )
            
            self.update_state(state='PROGRESS', meta={'current': 80, 'total': 100})
            task_service.update_task_status(
                task_id,
                'in_progress',
                progress=80,
                current_step='Fetching company officers'
            )
            
            officers = scraper.get_company_officers(
                company['company_number'],
                company['jurisdiction']
            )
            
            result_data = {
                'company_details': details,
                'officers': officers,
                'search_results': companies
            }
            
            task_service.complete_task(task_id, result_data=result_data)
            return {'status': 'completed', 'data': result_data}
        else:
            task_service.complete_task(
                task_id,
                result_data={'message': 'No company found'}
            )
            return {'status': 'completed', 'data': {'message': 'No company found'}}
            
    except Exception as e:
        logger.error(f"Task {task_id} failed: {str(e)}")
        task_service.fail_task(task_id, error_message=str(e))
        
        retry_count = self.request.retries
        if retry_count < self.max_retries:
            self.retry(countdown=2 ** retry_count * 60)
            
        raise

@celery.task(bind=True, max_retries=3)
def discover_contacts(self, task_id: str, company_domain: str) -> Dict[str, Any]:
    """Celery task to discover company contacts"""
    try:
        task_service.update_task_status(
            task_id,
            'in_progress',
            progress=0,
            current_step='Initializing contact discovery'
        )
        
        # Define discovery steps
        steps = [
            ('careers_page', 'Analyzing careers page'),
            ('about_page', 'Analyzing about page'),
            ('team_page', 'Analyzing team page'),
            ('contact_page', 'Analyzing contact page'),
            ('social_media', 'Checking social media profiles')
        ]
        
        contacts = []
        for i, (step_id, step_desc) in enumerate(steps):
            # Update progress for each step
            progress = int((i + 1) / len(steps) * 100)
            self.update_state(state='PROGRESS', meta={'current': progress, 'total': 100})
            task_service.update_task_status(
                task_id,
                'in_progress',
                progress=progress,
                current_step=step_desc
            )
            
            # TODO: Implement actual contact discovery logic
            # For now, just simulating work
            import time
            time.sleep(2)
        
        result_data = {
            'contacts': contacts,
            'scanned_pages': [step[0] for step in steps]
        }
        
        task_service.complete_task(task_id, result_data=result_data)
        return {'status': 'completed', 'data': result_data}
        
    except Exception as e:
        logger.error(f"Task {task_id} failed: {str(e)}")
        task_service.fail_task(task_id, error_message=str(e))
        
        retry_count = self.request.retries
        if retry_count < self.max_retries:
            self.retry(countdown=2 ** retry_count * 60)
            
        raise 